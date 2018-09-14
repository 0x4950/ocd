from json import dumps
from bson import ObjectId
from app import app, mongo
from os import environ, urandom
from random import randint, seed
from pymongo import MongoClient, ReturnDocument
from jsonpickle import set_encoder_options, encode, decode
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, request, flash, json, session, jsonify, make_response
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

usersCollection = mongo.db.users
gamesCollection = mongo.db.games

socketio = SocketIO(app)

login_manager = LoginManager()  # Instantiating a login manager
login_manager.init_app(app)  # Telling login manager about our Flask app
login_manager.login_view = "login"

class User(UserMixin):
  def __init__(self, username=None, id=None):
    self.username = username
    self.id = id

  def get_by_username_w_password(self, username):
    try:
      dbUser = usersCollection.find_one({'username': username})

      if dbUser:
        self.username = dbUser['username']
        self.password = dbUser['password']
        self.id = str(dbUser['_id'])
        return self
      else:
          return None
    except:
      return None

  def get_by_id(self, id):
    dbUser = usersCollection.find_one({'_id': ObjectId(id)})

    if dbUser:
      self.username = dbUser['username']
      self.id = str(dbUser['_id'])
      return self
    else:
      return None

@login_manager.user_loader
def user_loader(id):
  if id is None:
	  redirect('/login')

  user = User()
  user.get_by_id(id)
  return user


@app.route("/", methods=['GET', 'POST'])
def login():
  # If the user is already signed in, redirect him Dashboard.
  if current_user.is_authenticated:
    return redirect(url_for('dashboard'))

  if request.method == 'POST':
    form_username = request.form['username']
    userObj = User()
    user = userObj.get_by_username_w_password(form_username)
    if user and check_password_hash(user.password, request.form['password']):
        login_user(user)
        return redirect(url_for('dashboard'))
    else:
        flash(u'Incorrent password.', 'incorrect_password')

  return render_template('login_page.html')


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/create_account/', methods=['GET', 'POST'])
def create_account():
  if not usersCollection.find_one({'username': form.username.data}):
    hashed_password = generate_password_hash(form.password.data)
    usersCollection.insert({
      'username': form.username.data,
      'password': hashed_password,
      'participatingGames': []
    })
    flash(u'Account successfully created')
    return redirect(url_for('login'))
  else:
    flash(u'The username you have chosen is already in use.', 'used_username')
  return render_template('create_account.html')


@app.route("/dashboard/", methods=['GET', 'POST'])
@login_required
def dashboard():
  return render_template('dashboard.html')


@app.route('/api/get_and_create_games/', methods=['GET', 'POST'])
@login_required
def get_and_create_games():
  if request.method == "POST":
    msg = ''
    newCampName = request.json['name']
    name_conflict = gamesCollection.find_one({'$and':[{'name': newCampName},
    {'$or':[{'dm_id': current_user.id}, {'players.pid': current_user.id}]}]})

    if not name_conflict:
      # Insert the game document into 'gamesCollection' with info provided.
      game_id = gamesCollection.insert_one({
        'name': newCampName,
        'dm_id': current_user.id,
        'players': [],
        'staus': 'offline',
        'online_players': []
      })

      # Updating DM's participating games list with new game.
      usersCollection.update(
        {'username': current_user.username},
        {'$push': {'participatingGames': str(game_id.inserted_id)}})
    else:
      return make_response(jsonify({'msg': 'already_part'}), 600)
  games = []
  games_ids = usersCollection.find_one({'username': current_user.username})['participatingGames']

  for game_id in games_ids:
    game_dict = {}
    game_document = gamesCollection.find_one({'_id': ObjectId(game_id)})
    game_dict['name'] = game_document['name']
    game_dict['id'] = str(game_document['_id'])
    game_dict['created_time'] = game_document['_id'].generation_time
    games.append(game_dict)

  return jsonify(games)


@app.route('/game/<game_id_url>/')
@login_required
def game_page(game_id_url):
    players = []
    players_character = None

    # Search if the game exists in the games collection.
    if ObjectId.is_valid(game_id_url):
        # Check if the game exists.
        if gamesCollection.find_one({'_id': ObjectId(game_id_url)}):
            game = gamesCollection.find_one({'_id': ObjectId(game_id_url)})

            if belonger(game_id_url):
                # Retrieve DM's username.
                dm_username = usersCollection.find_one(
                    {'_id': game['dm_id']}, {'_id': 0, 'username': 1})

                # Pull players info from the users collection.
                for player in game['players']:
                    player_dict = {}
                    player_dict['username'] = usersCollection.find_one(
                        {'_id': ObjectId(player['_id'])})['username']

                    if player['character']:
                        player_dict['character'] = characters_collection.find_one(
                            {'_id': ObjectId(player['character'])})
                    else:
                        player_dict['character'] = None

                    if player_dict['username'] == current_user.username:
                        players_character = player_dict['character']

                    players.append(player_dict)

                return render_template('gamePage.html', game_id=game, players=players,
                                       dm_username=dm_username,
                                       players_character=players_character)
            else:
                flash(u'You do not participate in this game')
        else:
            flash(u'This game does not exist.')
    else:
        flash(u'This game does not exist')
    return redirect(url_for('dashboard'))


@app.route('/game/<game_id_url>/createCharacter', methods=['GET', 'POST'])
@login_required
def character_creation_page(game_id_url):
    error = None
    character_creation_form = CharacterCreationForm()

    if character_creation_form.validate_on_submit():
        try:
            # Call creator from genesis and initialize character.
            character_object = creator(character_creation_form,
                                       current_user.username, game_id_url)

            # Encoder options.
            set_encoder_options('json', sort_keys=True, indent=2)

            # Encode Character object - Turn the object dictionary into a string.
            character_string = encode(character_object, unpicklable=False)

            # Recreate a Python object from a JSON str.
            character_json = decode(character_string)

            # Insert into the database.
            characters_collection.replace_one(
                {'game_id': game_id_url, 'player_name': current_user.username},
                character_json, upsert=True)

            # Encode Character object - Turn the object dictionary into a string.
            character_object_json = json.loads(encode(character_object))

            # Insert into the database.
            character_python_objects_collection.replace_one(
                {'game_id': game_id_url, 'player_name': current_user.username},
                character_object_json, upsert=True)

            # Find the id of the logged in player.
            user_id = usersCollection.find_one(
                {'username': current_user.username}, {'_id': 1})

            ver = characters_collection.find_one(
                {'game_id': game_id_url, 'player_name': current_user.username},
                {'_id': 1})['_id']

            # Save the player in the game document.
            gamesCollection.update_one(
                {'_id': ObjectId(game_id_url), 'players._id': user_id['_id']},
                {"$set": {"players.$.character": ObjectId(ver)}})

            return redirect(url_for('game_page', game_id_url=game_id_url))
        except CustomException as e:
            # Pass the error to the template, so it can be flashed to the user.
            error = e.args[0]

    with open('static/form_vars.json') as json_data:
        classes = json.load(json_data)

    return render_template('index.html',
                           character_creation_form=character_creation_form, classes=classes, error=error)


@app.route('/game/<game_id_url>/npc_creation', methods=['GET', 'POST'])
@login_required
def npc_creation(game_id_url):
    # Initialise NPC Creation form
    npc_creation_form = NPCCreation(csrf_enabled=False)

    # If the form validates.
    if npc_creation_form.validate_on_submit():
        # Insert new NPC into database
        npcsCollection.insert_one({'npc_name': npc_creation_form.npc_name.data,
                                   'npc_description': npc_creation_form.npc_description.data,
                                   'ability_scores': npc_creation_form.npc_ability_scores.data,
                                   'game_id': ObjectId(game_id_url)})
        # Return to game page
        return redirect(url_for('npc_creation', game_id_url=game_id_url))

    npcs_list = npcsCollection.find({'game_id': ObjectId(game_id_url)})

    return render_template('npc_creation.html', npc_creation_form=npc_creation_form,
                           npcs_list=npcs_list, game_id=game_id_url)

@app.route('/game/<game_id_url>/delete_npc/', methods=['GET'])
@login_required
def delete_npc(game_id_url):
    npc_name = request.args.get('npc_name')

    npcsCollection.delete_one({'game_id': ObjectId(game_id_url), 'npc_name': npc_name})

    return redirect(url_for('npc_creation', game_id_url=game_id_url))

@app.route('/game/<game_id_url>/session/')
@login_required
def session_page(game_id_url):
    npcs = []
    dm_username = False
    users_player = None
    game = None

    if ObjectId.is_valid(game_id_url):  # If game id is valid
        # Retrieve game document from the database.
        game = gamesCollection.find_one({'_id': ObjectId(game_id_url)})

    if game:  # If the game is found
        if belonger(game_id_url):  # Check if player participates in this game
            # If the user is the dm let the template know.
            game_dm_name = usersCollection.find_one(
                {'_id': game['dm_id']}, {'username': 1})['username']

            if game_dm_name == current_user.username:
                dm_username = True
                # Set the field 'status' to online, so players can join the game.
                gamesCollection.update_one({'_id': game['_id']}, {"$set": {"status": 'online'}})

            if game['status'] == 'online' or dm_username is True:
                for player in game['players']:  # For each player retrieve characters
                    if player['character']:
                        # Get character from characters collection
                        char = characters_collection.find_one({'_id': player['character']})

                        # Check if the character exists.
                        if char:
                            # If character belongs to logged user inform the template
                            if char['player_name'] == current_user.username:
                                users_player = char['name']
                                session['users_player'] = char['name']

                # Get online players from the database.
                characters = gamesCollection.find_one({'_id': game['_id']},
                                                      {'online_players': 1})['online_players']

                # Load NPCS from the database.
                for npc in npcsCollection.find({'game_id': game['_id']},
                                               {'_id': 0, 'npc_name': 1, 'npc_description': 1}):
                    npcs.append(npc)

                # Save variables to session.
                session['game_id'] = game_id_url

                return render_template('session_page.html', game=game, dm_username=dm_username, characters=characters,
                                       npcs=npcs, users_player=users_player)
            else:
                flash(u'This session is offline.')
                return redirect(url_for('game_page', game_id_url=game_id_url))
        flash(u'You do not participate in this game.')
        return redirect(url_for('dashboard'))
    flash(u'This game does not exist.')
    return redirect(url_for('dashboard'))


@app.route('/game/<game_id_url>/session/combat_page')
@login_required
def combat_page(game_id_url):
    game = None
    user_is_dm = False
    users_player = None
    weapons = []
    abilities = []
    character_participating_in_combat = False
    character_initiated_position = False
    my_character = None
    my_character_spells = []

    # If the document id is valid
    if ObjectId.is_valid(game_id_url):
        # Retrieve game document from the database
        game = gamesCollection.find_one({'_id': ObjectId(game_id_url)})

    # If the game is found in the database.
    if game:
        # Check if player participates in this game
        if belonger(game_id_url):
            # Retrieve the name of the DM from database
            game_dm_name = usersCollection.find_one({'_id': ObjectId(game['dm_id'])}, {'username': 1})['username']
            if game_dm_name == current_user.username:
                # Let the template know if user is the DM.
                user_is_dm = True

            # Retrieve combat document from the database.
            combat_session = combat_session_monsters_collection.find_one({'game_id': game['_id']})

            if combat_session:
                # Let template and session variable know which character is his/hers.
                for character in combat_session['character_documents']:
                    character.pop('_id', None)
                    if character['type'] == 'player_character':
                        if character['player_name'] == current_user.username:
                            my_character = character

                # If this is not the DM, but a player with an existing character.
                if my_character:
                    users_player = my_character['combat_identifier']
                    
                    session['users_player'] = users_player

                    # If character is already set on the map let the template know, so it disables it.
                    if combat_session_monsters_collection.find_one(
                            {'game_id': ObjectId(game['_id']),
                            'character_documents': {'$elemMatch': {'combat_identifier': users_player, 'position': {'$ne': None}}}}):
                        character_initiated_position = True

                    # Pass abilities information to the template.
                    for ability in my_character['class_abilities']:
                        temp_ability = abilities_collection.find_one({'name': ability}, {'_id': 0})
                        if temp_ability:
                            abilities.append(temp_ability)

                    # Pass the spell infrmation to the template.
                    if 'prepared_spells' in my_character:
                        for spell in my_character['prepared_spells']:
                            temp_spell = spells_collection.find_one({'name': spell}, {'_id': 0})
                            if temp_spell:
                                my_character_spells.append(temp_spell)

                        for spell in my_character['cantrips']:
                            temp_spell = spells_collection.find_one({'name': spell}, {'_id': 0})
                            if temp_spell:
                                my_character_spells.append(temp_spell)

                # Check if player is participating in the combat session with his character.
                if combat_session_monsters_collection.find_one({'game_id': ObjectId(game['_id']),
                                                                'character_documents.combat_identifier': users_player}):
                    character_participating_in_combat = True

                # Pass currently playing character/monster to the template.
                currently_playing_character = combat_session_monsters_collection.find_one(
                    {'game_id': ObjectId(game['_id'])})['currently_playing_character']

                # Pass type of currently playing character to the the template.
                currently_playing_is = combat_session_monsters_collection.find_one(
                    {'game_id': ObjectId(game['_id'])})['currently_playing_is']

                # Pass weapon information to the template.
                for weapon in weapons_collection.find({}, {'_id': 0, 'name': 1, 'properties': 1}):
                    weapons.append(weapon)

                # Set session variable for game id.
                if user_is_dm or character_participating_in_combat:
                    session['game_id'] = game_id_url

                    return render_template('combat_page.html', game_id_url=game_id_url, user_is_dm=user_is_dm,
                                        users_player=users_player,
                                        character_initiated_position=character_initiated_position,
                                        currently_playing_character=currently_playing_character,
                                        currently_playing_is=currently_playing_is, weapons=weapons,
                                        characters=combat_session['character_documents'],
                                        my_character_abilities=abilities,
                                        round=combat_session['round'], time=combat_session['time'],
                                        initiative_order=combat_session['initiative_order'],
                                        game=game, my_character_spells=my_character_spells)
            else:
                flash("Session is not in combat.")
                return redirect(url_for('session_page', game_id_url=game_id_url))
        else:
            flash("You do not participate in this game.")
    else:
        flash("This game does not exist.")
    return redirect(url_for('dashboard'))


@app.route('/game/<game_id_url>/exit_session/')
@login_required
def exit_session(game_id_url):
    # Set the game variable back to 'offline', so players cannot join.
    gamesCollection.update_one({'_id': ObjectId(game_id_url)}, {"$set": {"status": 'offline'}})
    
    # Inform joined players that the session is over.
    dc_msg = dict()
    dc_msg['type'] = 'exit_session'
    socketio.emit('message', dc_msg, broadcast=True, namespace='/session_page_namespace')

    return redirect(url_for('game_page', game_id_url=game_id_url))

@app.route('/game/<game_id_url>/exit_combat/')
@login_required
def exit_combat(game_id_url):
    msg = dict()

    # Load characters from the database.
    characters = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(game_id_url)})['character_documents']

    # Update characters documents.
    for character in characters:
        if character['type'] == 'player_character':
            db_update_object = {}

            db_update_object['experience_points'] = character['experience_points']
            db_update_object['current_hit_points'] = character['current_hit_points']
            db_update_object['burned_spells_abilities'] = character['burned_spells_abilities']
            db_update_object['health_status'] = character['health_status']
            db_update_object['rest_status'] = character['rest_status']

            if 'spells_slots_used' in character:
                db_update_object['spell_slots_used'] = character['spell_slots_used']

            characters_collection.update_one(
                {'name': character['name'],
                 'game_id': character['game_id'],
                 'player_name': character['player_name']},
                {'$set': db_update_object})

            character_python_objects_collection.update_one(
                {'name': character['name'],
                 'game_id': character['game_id'],
                 'player_name': character['player_name']},
                {'$set': db_update_object})

            check_experience_points(character['game_id'], character['name'])

    # Delete combat document.
    combat_session_monsters_collection.remove({'game_id': ObjectId(game_id_url)})

    # Redirect players to the session page.
    msg['type'] = 'exit_combat'
    socketio.emit('message', msg, broadcast=True, namespace='/combat_page_namespace')

    # Redirect the DM to the session page.
    return redirect(url_for('session_page', game_id_url=game_id_url))

@app.route('/game/<game_id_url>/prepared_spells', methods=['GET', 'POST'])
@login_required
def prepared_spells(game_id_url):
    character_document = None
    selected_spells = set()
    spells_list = []
    spell_level_cap = 0
    error = None

    # Check if character belongs to the game.
    if belonger(game_id_url):
        # TODO Check if character has spells.

        # Retrive character document from the database.
        character_document = characters_collection.find_one(
            {'game_id': game_id_url, 'player_name': current_user.username})

        if request.method == 'POST':
            # Get all the checked spells.
            for item in request.form:
                selected_spells.add(item)

            try:
                # Call function to set the prepared spells.
                result = spells.set_prepared_spells(character_document, selected_spells)
                characters_collection.update_one(
                    {'name': character_document['name']},
                    {'$set': {'prepared_spells': list(result)}})
                return redirect(url_for('game_page', game_id_url=game_id_url))
            except spells.PrepareSpellException as e:
                error = e.args[0]
                flash(error)

        # Retrieve all spells the database.
        if character_document['level'] >= 5:
            spell_level_cap = 3
        elif character_document['level'] >= 3:
            spell_level_cap = 2
        else:
            spell_level_cap = 1

        for spell in spells_collection.find(
                {'$and': [{'level': {'$lte': spell_level_cap},
                          'class': {'$in': [character_document['class']]}}]}):
            spells_list.append(spell)

        return render_template('prepared_spells.html', game_id_url=game_id_url,
                               character=character_document, spells=spells_list, error=error)
    else:
        flash("You do not participate in this game.")

    return redirect(url_for('dashboard'))

@app.route('/game/<game_id_url>/level_up', methods=['GET', 'POST'])
@login_required
def level_up(game_id_url):
    error = None
    character_document = None
    argument_list = dict()
    new_ability_scores = {'strength': 0,
                          'dexterity': 0,
                          'constitution': 0,
                          'intelligence': 0,
                          'wisdom': 0,
                          'charisma': 0}

    # Check if character belongs to the game.
    if belonger(game_id_url):
        # Retrive character document from the database.
        character_document = characters_collection.find_one(
            {'game_id': game_id_url, 'player_name': current_user.username})

        character_document_id = character_document['_id']
        del character_document['_id']
        
        if request.method == 'POST':
            # Retrieve the form inputs.
            f = request.form

            for key in f.keys():
                if key in new_ability_scores:
                    for value in f.getlist(key):
                        new_ability_scores[key] = value
                    argument_list['new_ability_scores'] = new_ability_scores
                else:
                    for value in f.getlist(key):
                        argument_list[key] = value

            # Retrieve the document from the database, as a dictionary
            character_python_object = character_python_objects_collection.find_one(
                {'game_id': game_id_url,
                'player_name': current_user.username,
                'name': character_document['name']})

            # Save the document id, so it can be replaced later.
            character_object_document_id = character_python_object['_id']
            del character_python_object['_id']

            # Turn the dictionary into a string.
            character_python_object = dumps(character_python_object)

            # Re-create a Character object from that string.
            character_object = decode(character_python_object)

            try:
                # Call the level_up method of the Character object.
                character_object.level_up(**argument_list)

                # Encoder options.
                set_encoder_options('json', sort_keys=True, indent=2)

                # Encode Character object - Turn the object dictionary into a string.
                character_string = encode(character_object, unpicklable=False)

                # Recreate a Python object from a JSON str.
                character_json = decode(character_string)

                # Insert into the database.
                characters_collection.replace_one(
                    {'_id': character_document_id}, character_json)

                # Encode Character object - Turn the object dictionary into a string.
                character_object_json = json.loads(encode(character_object))

                # Insert into the database.
                character_python_objects_collection.replace_one(
                    {'_id': character_object_document_id}, character_object_json)

                return redirect(url_for('game_page', game_id_url=game_id_url))
            except Exception as e:
                error = e.args[0]
                flash(error)

        return render_template('level_up.html', game_id_url=game_id_url,
                               character=character_document, error=error)
    else:
        flash("You do not participate in this game.")
        return redirect(url_for('dashboard'))


@app.route('/game/<game_id_url>/prepared_weapons', methods=['GET', 'POST'])
@login_required
def prepared_weapons(game_id_url):
    character_document = None
    selected_weapons = list()
    error = None

    # Check if character belongs to the game.
    if belonger(game_id_url):

        # Retrive character document from the database.
        character_document = characters_collection.find_one(
            {'game_id': game_id_url,
             'player_name': current_user.username})

        if request.method == 'POST':
            request_weapons = dict(request.form)

            for item in request_weapons:
                for i in range(len(request_weapons[item])):
                    selected_weapons.append(item)

            try:
                # Call function to set the prepared weapons.
                result = attacks.set_prepared_weapons(character_document, selected_weapons)

                # Update the database.
                characters_collection.update_one(
                    {'game_id': game_id_url, 'name': character_document['name']},
                    {'$set': {'equipped': list(result)}})

                return redirect(url_for('game_page', game_id_url=game_id_url))
            except attacks.PrepareWeaponException as e:
                error = e.args[0]
                flash(error)

        return render_template('prepared_weapons.html', game_id_url=game_id_url,
                               character=character_document, spells=spells, error=error)
    else:
        flash("You do not participate in this game.")

    return redirect(url_for('dashboard'))

@socketio.on('connect', namespace='/session_page_namespace')
def session_character_connected():
    # Join the room.
    join_room(session['game_id'])

    if 'users_player' in session and session['users_player']:
        # Insert player's character into 'online_players' list
        # and return the updated document.
        game = gamesCollection.find_one_and_update(
            {'_id': ObjectId(session['game_id'])},
            {"$addToSet": {"online_players": session['users_player']}},
            return_document=ReturnDocument.AFTER)

        emit('joined_player', {'characters': game['online_players']}, room=session['game_id'],
             broadcast=True)


@socketio.on('disconnect', namespace='/session_page_namespace')
def session_character_disconnected():
    # Leave the room.
    leave_room(session['game_id'])

    if 'users_player' in session and session['users_player']:
        # Remove player's character from 'online_players' list
        # and return the updated document.
        characters = gamesCollection.find_one_and_update(
            {'_id': ObjectId(session['game_id'])},
            {"$pull": {"online_players": session['users_player']}},
            return_document=ReturnDocument.AFTER)['online_players']

        emit('joined_player', {'characters': characters}, room=session['game_id'], broadcast=True)


@socketio.on('connect', namespace='/combat_page_namespace')
def combat_character_connected():
    # Join the room.
    join_room(session['game_id'])


@socketio.on('disconnect', namespace='/combat_page_namespace')
def combat_character_disconnected():
    # Leave the room.
    leave_room(session['game_id'])


@socketio.on('load_combat_characters', namespace='/session_page_namespace')
def load_combat_characters(characters_selected):
    character_document = None
    msg = dict()

    if not combat_session_monsters_collection.find_one({'game_id': ObjectId(session['game_id'])}):
        combat_session_monsters_collection.insert_one(
            {'game_id': ObjectId(session['game_id']),
             'online_combat_characters': [], 'character_documents': [],
             'combat_characters': [],
             'time': 0,
             'round': 0,
             'currently_playing_character': None,
             'currently_playing_is': None,
             'initiative_order': None,
             'positions_occupied': []})

        for counter, character in enumerate(characters_selected):
            # Load the character document from the database.
            character_document = characters_collection.find_one({'name': character})

            if character_document:
                # Initialize values needed for combat.
                character_document['combat_identifier'] = gen_combat_id(character_document['name'],
                                                                        counter)
                character_document['displacement_left'] = character_document['speed']
                character_document['position'] = None
                character_document['previous_casted_spell'] = None
                character_document['weapon_used'] = None
                character_document['spell_used'] = None
                character_document['attack_points'] = character_document['attack_points_per_turn']
                character_document['actions_used'] = 0
                character_document['bonus_actions_used'] = 0
                character_document['rest_status'] = "unrested"

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id'])},
                    {'$push': {'character_documents': character_document}})

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id'])},
                    {'$push': {'combat_characters': character_document['combat_identifier']}})

    # Message to redirect users to combat session page.
    msg['type'] = "enter_combat"
    msg['combat_characters'] = characters_selected
    emit('message', msg, broadcast=True)


@socketio.on('my event', namespace='/session_page_namespace')
def handle_message(message):
    """
    This function will be called, when a user(DM) uploads an image.
    It will rebroadcast the image back to all participating the session.
    """
    emit('dis', message, broadcast=True)


@socketio.on('ability_check_initiated', namespace='/session_page_namespace')
def ability_check_initiated(dm_check_info):
    """
    This function will be called when a user(DM) calls for an Ability Check.
    It will "release" the buttons for the users(players) and send the variables for comparison.
    """
    log_msg = dict()  # WINNER, LOSER, ROLLS
    log_msg['type'] = dm_check_info['type']

    for character in dm_check_info['characters']:
        if npcsCollection.find_one({'npc_name': character['name']}):
            result = dice_rolling(character['name'], character['skill'])
            log_msg['result'] = result
            log_msg['character'] = character['name']
            log_msg['skill'] = character['skill']
            emit("message", log_msg, broadcast=True)
        else:
            log_msg['opponent'] = character['name']

    emit('enable_rolls', dm_check_info, broadcast=True)


@socketio.on('ability_check_dice_roll', namespace='/session_page_namespace')
def ability_check_dice_roll(character, player_check_info):
    """
    This function will be called when a user(player) pressed the d20 button.
    It will generate a random number and check if it passes the selected DC/opponent's number.
    """

    log_msg = dict()  # WINNER, LOSER, ROLLS
    log_msg['type'] = player_check_info['type']

    if player_check_info['type'] == 'ability_check':
        dc = player_check_info['difficulty_class']
        skill = player_check_info['characters'][0]['skill']

        result = dice_rolling(character, skill)

        if result >= dc:
            log_msg['status'] = 1  # Player wins
        elif result < dc:
            log_msg['status'] = 2  # Dungeon Master wins

        log_msg['result'] = result
        log_msg['skill'] = skill
        log_msg['character_name'] = character

    elif player_check_info['type'] == 'contest':
        for char in player_check_info['characters']:
            if characters_collection.find_one(
                    {'name': char['name'],
                     'player_name': current_user.username}):
                result = dice_rolling(char['name'], char['skill'])

                log_msg['character'] = char['name']
                log_msg['skill'] = char['skill']

                log_msg['result'] = result
            else:
                log_msg['opponent'] = char['name']

    emit("message", log_msg, broadcast=True)


@socketio.on('time_changer', namespace='/session_page_namespace')
def time_changer(current_time):
    # Save the time to the database.
    gamesCollection.update_one(
        {'_id': ObjectId(session['game_id'])}, {'$set': {'time': current_time}})

    # Simply retransmit the selected time to all clients.
    emit('update_time', current_time, broadcast=True)


@socketio.on('server_exp_points', namespace='/session_page_namespace')
def server_exp_points(characters_list, exp_to_award):
    exp_msg = {}

    for character in characters_list:
        characters_collection.update_one(
            {'game_id': session['game_id'], 'name': character},
            {"$inc": {"experience_points": exp_to_award}})

        character_python_objects_collection.update_one(
            {'game_id': session['game_id'], 'name': character},
            {"$inc": {"experience_points": exp_to_award}})

        check_experience_points(session['game_id'], character)

    exp_msg['type'] = 'exp'
    exp_msg['awarded_characters'] = characters_list
    exp_msg['amount'] = exp_to_award

    emit('message', exp_msg, broadcast=True)

@socketio.on('server_rest', namespace='/session_page_namespace')
def server_rest(characters_list):
    rest_msg = {}

    for character in characters_list:
        character_document = characters_collection.find_one(
            {'game_id': session['game_id'], 'name': character})

        maximum_character_hit_points = character_document['maximum_hit_points']

        # See if character has maximum hit points buff.
        if 'maximum_hit_points' in character_document['buffs']['temporary']:
            for buff in character_document['buffs']['temporary']['maximum_hit_points']:
                # Increase maximum hit points of the character by the buff amount.
                maximum_character_hit_points += buff['amount']

        characters_collection.update_one(
            {'game_id': session['game_id'], 'name': character},
            {"$set": {"rest_status": "rested",
                      "death_saving_throws_attempts": [0, 0],
                      "burned_spells_abilities": [],
                      "spell_slots_used": [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      "current_hit_points": maximum_character_hit_points}})

        characters_collection.update_one(
            {"$or": [{ "health_status": "stable"}, {"health_status": "unconscious"}]},
            {"$set": {"health_status": "alive"}})

        rest_msg['type'] = 'rest'
        rest_msg['rested_characters'] = characters_list

        emit('message', rest_msg, broadcast=True)


@socketio.on('monster_loaded', namespace='/combat_page_namespace')
def load_monster(monster_loaded):
    # Retrieve monster information from database
    monster_stat_block = monsters_collection.find_one(
        {'name': monster_loaded['name'].lower().replace(" ", "_")}, {'_id': 0})

    # Set unique identifiers for each monster
    monsters = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])},
        {'character_documents': 1})['character_documents']

    monster_stat_block['combat_identifier'] = gen_combat_id(monster_stat_block['name'],
                                                            len(monsters))

    # If position is not already occupied by another monster.
    if not combat_session_monsters_collection.find_one(
            {'game_id': ObjectId(session['game_id']),
             'positions_occupied': {'$in': [monster_loaded['position']]}}):
        # If the position coming from the page is valid.
        if monster_loaded['position'] in range(0, 64):
            monster_stat_block['type'] = 'monster'
            monster_stat_block['health_status'] = 'alive'
            monster_stat_block['position'] = monster_loaded['position']
            monster_stat_block['displacement_left'] = monster_stat_block['speed']
            monster_stat_block['current_hit_points'] = monster_stat_block['hit_points']
            monster_stat_block['maximum_hit_points'] = monster_stat_block['current_hit_points']
            monster_stat_block['attack_points'] = monster_stat_block['attack_points_per_turn']
            monster_stat_block['actions_used'] = 0
            monster_stat_block['displayed_hp_status'] = 'Undamaged'
            monster_stat_block['weapon_used'] = None

            # Push monster to combat session monsters database
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id'])},
                {'$push': {'character_documents': monster_stat_block,
                           'positions_occupied': monster_loaded['position']}})

            emit("display_loaded_monster", monster_stat_block, broadcast=True)

        else:
            # TODO
            # Error code for invalid position.
            pass
    else:
        # TODO
        # Complete with error message for the DM to know what went wrong.
        pass

@socketio.on('character_position', namespace='/combat_page_namespace')
def character_position(character_position_info):
    distance = 0
    message = {'msg': None}

    character_identifier = character_position_info['character_identifier']
    new_position = character_position_info['character_position']

    # Retrieve character/monster document.
    character_document = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id']),
         'character_documents.combat_identifier': character_identifier},
        {'_id': 0, 'character_documents.$': 1})['character_documents'][0]

    # Retrieve occupied positions as a list.
    occupied_positions = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])},
        {'_id': 0, 'positions_occupied': 1})['positions_occupied']

    old_position = character_document['position']

    if new_position != old_position:
        if character_document['health_status'] == 'alive':
            # If position is not already occupied by another character/monster.
            if new_position not in occupied_positions:
                # If the position coming from the page is valid.
                if new_position in range(0, 64):
                    # Calculate distance character want to travel.
                    if old_position is not None:
                        distance = euclidean_distance(old_position, new_position)

                    if distance <= character_document['displacement_left']:
                        if old_position in occupied_positions:
                            occupied_positions.remove(old_position)
                        occupied_positions.append(new_position)

                        character_documents = combat_session_monsters_collection.find_one_and_update(
                            {'game_id': ObjectId(session['game_id']),
                            'character_documents.combat_identifier': character_identifier},
                            {'$set': {'positions_occupied': occupied_positions,
                                    'character_documents.$.position': new_position},
                            '$inc': {'character_documents.$.displacement_left': -distance}},
                            {'_id': 0, 'character_documents': 1, },
                            return_document=ReturnDocument.AFTER)['character_documents']

                        for character in character_documents:
                            if character['combat_identifier'] == character_identifier:
                                character_document = character

                        # Load old position to sent to client.
                        character_document['old_position'] = old_position

                        # Delete '_id' field from player characters.
                        if '_id' in character_document:
                            del character_document['_id']

                        emit("display_loaded_" + character_document['type'], character_document, broadcast=True)
                    else:
                        message['msg'] = "You are not fast enough to move to that position."
                else:
                    message['msg'] = "That location is out of bounds."
            else:
                message['msg'] = "That position is already occupied."
        else:
            message['msg'] = "You cannot move in your condition."

        emit("message", message)


@socketio.on('initiate_initiative_rolls', namespace='/combat_page_namespace')
def initiate_initiative_rolls():
    rolls = dict()

    # Retrieve document from the database.
    combat_document = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])})

    # Roll a dice for each character/monster.
    for character in combat_document['character_documents']:
        rolls[character['combat_identifier']] = roll_initiative(character)

    # Sort by values and save to list
    initiative_order = sorted(rolls, key=rolls.get)
    initiative_order.reverse()

    # Check whether the playing entity is either a "Character" or a "Monster".
    for character in combat_document['character_documents']:
        if character['combat_identifier'] == initiative_order[0]:
            currently_playing_is = character['type']

    # Push initiative order variables into the database document.
    combat_session_monsters_collection.update_one(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'initiative_order': initiative_order,
                  'currently_playing_character': initiative_order[0],
                  'currently_playing_is': currently_playing_is}})

    # Initialise turns & rounds.
    turns_n_rounds(ObjectId(session['game_id']), initiative_order)

    # Push the Initiative Order to the users.
    emit('display_initiative_order', {'initiative_order': initiative_order,
                                      'currently_playing_character': initiative_order[0],
                                      'currently_playing_is': currently_playing_is,
                                      'round': 1}, broadcast=True)


@socketio.on('next_turn', namespace='/combat_page_namespace')
def next_turn(data):
    # Increase the 'turn' counter and the time and then load the updated document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$inc': {'turn': 1, 'time': 6}},
        return_document=ReturnDocument.AFTER)

    # Check if the end of a turn has arrived.
    if combat_document['turn'] >= combat_document['round_length']:
        # Set the turn to zero again.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id'])}, {'$set': {'turn': 0}})

        # Increase the round counter.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id'])}, {'$inc': {'round': 1}})

        for character in combat_document['character_documents']:
            if character['health_status'] == 'alive' or character['health_status'] == 'unconscious':
                # Reset values for attacks, spells, movement for each character/monster.
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': character['combat_identifier']},
                    {'$set': {'character_documents.$.displacement_left': character['speed'],
                              'character_documents.$.attack_points': character['attack_points_per_turn'],
                              'character_documents.$.actions_used': 0,
                              'character_documents.$.bonus_actions_used': 0,
                              'character_documents.$.previous_casted_spell': None,
                              'character_documents.$.weapon_used': None,
                              'character_documents.$.spell_used': None}})

                # Pull temporary buffs that have expired.
                if 'buffs' in character:
                    if 'temporary' in character['buffs']:
                        for key in character['buffs']['temporary']:
                            for buff in character['buffs']['temporary'][key]:
                                if buff['expires'] < combat_document['time']:
                                    character['buffs']['temporary'][key].remove(buff)

                # Update character's document with updated buffs dictionary.
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': character['combat_identifier']},
                    {'$set': {'character_documents.$.buffs': character['buffs']}})

                # Check for overtime damage effects that have expired.
                for debuff in character['debuffs']['overtime_effects']:
                    if debuff['type'] == 'damage' and debuff['expires'] < combat_document['time']:
                        apply_damage(debuff['amount'], ObjectId(session['game_id']),
                                     character, debuff['damage_type'])

                        # If the debuff expires on use remove it from the debuffs list.
                        if debuff['expires_on_use']:
                            combat_session_monsters_collection.update_one(
                                {'game_id': ObjectId(session['game_id']),
                                 'character_documents.combat_identifier': character['combat_identifier']},
                                {'$pull': {'character_documents.$.debuffs.overtime_effects': debuff}})

        # Retrieve the updated document
        combat_document = combat_session_monsters_collection.find_one(
            {'game_id': ObjectId(session['game_id'])})

    # Change 'currently_playing_character' saved in the database and reload the document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'currently_playing_character': combat_document['initiative_order'][combat_document['turn']]}},
        return_document=ReturnDocument.AFTER)

    # Check whether the playing entity is either a "Character" or a "Monster".
    currently_playing_is = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id']),
         'character_documents.combat_identifier': combat_document['currently_playing_character']},
        {'_id': 0, 'character_documents.$.type': 1})['character_documents'][0]['type']

    # Change 'currently_character_is' saved in the database and reload the document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'currently_playing_is': currently_playing_is}},
        return_document=ReturnDocument.AFTER)

    emit('changing_turn', {'currently_playing_character': combat_document['currently_playing_character'],
                           'currently_playing_is': combat_document['currently_playing_is'],
                           'time': combat_document['time'], 'round': combat_document['round']},
                           broadcast=True)


@socketio.on('action', namespace='/combat_page_namespace')
def character_monster_action(data):
    targets = []
    attack_range_permitted = True
    critical = False
    update_action = True
    rdy_to_attack = False
    bad_condition = True
    rdy_to_cast_spell = False
    rdy_to_use_ability = False
    this_spell_is_cantrip = False
    previous_casted_spell_is_cantip = False
    weapon_property = None
    valid_health_points = True
    invalid_attack_points = False
    weapon_is_melee_light =  False
    different_weapon = False
    bonus_action_attack = False
    weapon_uniqueness_counter = 0
    actor_melee_light_weapon_used = False
    db_search_object = {}
    db_update_object = {}
    spell = None
    subability = None
    self_casted = False
    chars_distance = 9000
    allowed_distance = 0
    msg = {}
    broadcast_value = False

    # Retrieve combat document from the database.
    combat_document = combat_session_monsters_collection.find_one({'game_id': ObjectId(session['game_id'])})
    combat_characters = combat_document['character_documents']

    # Check if targets and actor is either a monster or a character.
    for character in combat_characters:
        if character['combat_identifier'] == data['actor']:
            actor = character
        if 'targets' in data:
            for target in data['targets']:
                if character['combat_identifier'] == target:
                    targets.append(character)

    # Retrieve weapon/spell information from the database.
    if 'weapon' in data:
        weapon = weapons_collection.find_one({'name': data['weapon']})

        # Check if the weapon is used with a certain property(e.g. melee/thrown)
        if 'weapon_property' in data:
            weapon_property = data['weapon_property']
        
        # Check if the weapon is melee and has the 'light' property.
        if 'light' in weapon['properties'] and weapon['attack_range'] == 'melee':
            weapon_is_melee_light = True

        # Check if weapon is different from the one used in character's action.
        for w in actor['weapons']:
            if w == data['weapon']:
                weapon_uniqueness_counter += 1
        if weapon_uniqueness_counter > 1 or data['weapon'] != actor['weapon_used']:
            different_weapon = True

        # Check if the actor is trying to attack with a weapon he is not supposed to.
        if (actor['attack_points'] - weapon['attack_points']) == 1:
            invalid_attack_points = True
        elif actor['attack_points'] < actor['attack_points_per_turn']:
            invalid_attack_points = True

        # Check if light weapon has already been used.
        if actor['weapon_used']:
            if weapons_collection.find_one(
                    {'name': actor['weapon_used'],
                     'attack_range': 'melee', 'properties': {'$in': ['light']}}):
                actor_melee_light_weapon_used = True

        # Set the distance allowed by the weapon.
        if (weapon['attack_range'] == 'melee' and not weapon_property) or weapon_property == 'melee' or weapon_property == 'versatile':
            allowed_distance = 5
        elif (weapon['attack_range'] == 'melee' and weapon_property == 'thrown') or weapon['attack_range'] == 'ranged':
            allowed_distance = weapon['long_range']
    elif 'spell' in data:
        spell = spells_collection.find_one({'name': data['spell']})

        # Get the subspell.
        if 'subspell' in data:
            subspell = data['subspell']

        # Save the spell distance.
        allowed_distance = spell['range']

        # Check for slot availability.
        available_slot = spells.check_slot_availability(actor, spell)

        # Check if the spell is a cantrip.
        if spell['level'] == 0:
            this_spell_is_cantrip = True

        # Check if previous spell used was cantrip.
        if actor['previous_casted_spell']:
            if spells_collection.find_one({'name': actor['previous_casted_spell'], 'level': 0}):
                previous_casted_spell_is_cantip = True
    elif 'ability' in data:
        ability = abilities_collection.find_one({'name': data['ability']})

        # Get the sub-ability.
        if 'sub_ability' in data:
            subability = abilities_collection.find_one({'name': data['sub_ability']})

        # Get the ability/subability distance.
        if subability:
            if subability['target'] == 'self_cast':
                self_casted = True
            else:
                allowed_distance = subability['range']
        else:
            if ability['target'] == 'self_cast':
                self_casted = True
            else:
                allowed_distance = ability['range']

    # Check if actor and targets have valid health statuses.
    if 'targets' in data:
        if actor['health_status'] == 'dead' or actor['health_status'] == 'unconscious':
            valid_health_points = False

        for target in targets:
            if target['health_status'] == 'dead':
                valid_health_points = False

    # Calculate the distance between the actor & the targets.
    if targets and actor:
        for target in targets:
            chars_distance = euclidean_distance(actor['position'], target['position'])

            # Check if the distance criterion is met.
            if (chars_distance > allowed_distance) or self_casted:
                attack_range_permitted = False

    # Check for conditions that prevent character from using his action.
    bad_condition = check_actor_condition(actor)

    if not bad_condition:
        if attack_range_permitted:
            if data['action'] == 'attack' or data['action'] == 'two_weapon_fighting':
                if valid_health_points:
                    if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
                        if not invalid_attack_points:
                            rdy_to_attack = True
                        else:
                            msg['msg'] = "You cannot make another attack on the same turn."
                    elif data['action_type'] == 'bonus_action' and actor['bonus_actions_used'] < actor['bonus_actions_per_turn']:
                        # Check if the weapons used in both attacks are light.
                        if actor_melee_light_weapon_used and weapon_is_melee_light:
                            # Check if weapons are different.
                            if different_weapon:
                                rdy_to_attack = True
                                bonus_action_attack = True
                            else:
                                msg['msg'] = "You cannot attack with the same weapon."
                        else:
                            msg['msg'] = "You have to use melee light weapons with both actions"
                    else:
                        msg['msg'] = "You have already used your action/bonus action for this turn"
                else:
                    msg['msg'] = "Both characters and monsters must be alive in order for that action."
            elif data['action'] == 'spell_cast' or data['action'] == 'bonus_action_spell_cast':
                if valid_health_points:
                    if data['action_type'] == 'action' and spell['action_use'] == 'action' \
                        and actor['actions_used'] < actor['actions_per_turn']:
                        if (not actor['previous_casted_spell']) or this_spell_is_cantrip:
                            if available_slot:
                                if spell['name'] not in actor['burned_spells_abilities']:
                                    rdy_to_cast_spell = True
                                else:
                                    msg['msg'] = "You must finish a short/long rest before using that spell again."
                            else:
                                msg['msg'] = "You do not have any more slots for a spell of this level."
                        else:
                            msg['msg'] = "You cannot perform that action."
                    elif data['action_type'] == 'bonus_action' and spell['action_use'] == 'bonus_action' \
                        and actor['bonus_actions_used'] < actor['bonus_actions_per_turn']:
                        if (not actor['previous_casted_spell']) or previous_casted_spell_is_cantip:
                            if available_slot:
                                if spell['name'] not in actor['burned_spells_abilities']:
                                    rdy_to_cast_spell = True
                                else:
                                    msg['msg'] = "You must finish a short/long rest before using that spell again."
                            else:
                                msg['msg'] = "You do not have any more slots for a spell of this level."
                        else:
                            msg['msg'] = "You cannot perform that action."
                    else:
                        msg['msg'] = "You have already used your action/bonus action for this turn."
                else:
                    msg['msg'] = "Both characters and monsters must be alive in order for that action."
            elif data['action'] == 'use_ability':
                # Check if the actor has used all his actions, or one is not needed.
                if (data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']) or \
                    ability['action_used'] == 'no_action':
                    # Check if the ability is has been used again.
                    if ability['name'] not in actor['burned_spells_abilities']:
                        rdy_to_use_ability = True
                    else:
                        msg['msg'] = "You must finish a short/long rest before using that spell again."
                else:
                    msg['msg'] = "You have already used your action/bonus action for this turn."
        else:
            msg['msg'] = "Target is out of range."
    else:
        msg['msg'] = "Your current condition does not allow you to use an action this turn."

    # Handle death saving throws for unconscious characters.
    if data['action'] == 'death_saving_throw':
        db_update_object = {}

        if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
            if actor['health_status'] == 'unconscious':
                # Death Saving Throw.
                death_saving_throw = attacks.death_saving_throw(actor)

                if death_saving_throw == 'passed':
                    actor['death_saving_throws_attempts'][0] += 1
                    msg["msg"] = "You have passed this round's death saving throw roll."
                elif death_saving_throw == 'failed':
                    actor['death_saving_throws_attempts'][1] += 1
                    msg["msg"] = "You have failed this round's death saving throw roll."
                elif death_saving_throw == 'one':
                    actor['death_saving_throws_attempts'][1] += 2
                    msg["msg"] = "You have rolled 1 this round's death saving throw roll."

                db_update_object['character_documents.$.death_saving_throws_attempts'] = actor['death_saving_throws_attempts']

                # Check if actor's status is changing.
                if death_saving_throw == 'twenty' or actor['death_saving_throws_attempts'][0] >= 3:
                    if death_saving_throw == 'twenty':
                        msg["msg"] = "You have rolled 20 on this round's death saving throw."
        
                    msg["msg"] += " Your character is now stable, but unconscious."
                    msg["type"] = "alive_by_attempts"

                    actor['health_status'] = 'stable'
                    db_update_object['character_documents.$.current_hit_points'] = 0
                elif actor['death_saving_throws_attempts'][1] >= 3:
                    msg["msg"] += " Your character is now dead."
                    msg['type'] = "dead_by_attempts"

                    actor['health_status'] = 'dead'

                if 'type' in msg:
                    if(msg['type'] == "alive_by_attempts") or (msg['type'] == "dead_by_attempts"):
                        # Remove the dead player character from the initiative order list,
                        # and decrease the round length by 1.
                        combat_session_monsters_collection.update_one(
                            {'game_id': ObjectId(session['game_id'])},
                            {'$pull': {'initiative_order': actor['combat_identifier']},
                                '$inc': {'round_length': -1}})

                db_update_object['character_documents.$.health_status'] = actor['health_status']

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$set': db_update_object,
                     '$inc': {'character_documents.$.actions_used': 1}})

                msg["msg"] += " Your current attempts are " + str(actor['death_saving_throws_attempts']) + "."
            else:
                msg['msg'] = "Character must be unconscious."
        else:
            msg['msg'] = "You have already used your action/bonus action for this turn."

    if data['action'] == 'don_shield' or data['action'] == 'doff_shield':
        if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
            if data['action'] == 'don_shield':
                try:
                    new_weapon_list = actor['equipped']
                    new_weapon_list.append('shield')

                    attack_weapon = attacks.set_prepared_weapons(actor, new_weapon_list)

                    combat_session_monsters_collection.update_one(
                        {'game_id': ObjectId(session['game_id']),
                        'character_documents.combat_identifier': actor['combat_identifier']},
                        {'$set': {'character_documents.$.equipped': attack_weapon}})
                    
                    msg['msg'] = "You have equipped the shield."
                except attacks.PrepareWeaponException as e:
                    error = e.args[0]
                    msg['msg'] = error
            elif data['action'] == 'doff_shield':
                if 'shield' in actor['equipped']:
                    # Remove the shield from character's equipped list.
                    combat_session_monsters_collection.update_one(
                        {'game_id': ObjectId(session['game_id']),
                        'character_documents.combat_identifier': actor['combat_identifier']},
                        {'$pull': {'character_documents.$.equipped': 'shield'}})
                    
                    msg['msg'] = "You no longer have a shield equipped."

            # Update actor's action/bonus action status.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                    'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': {'character_documents.$.actions_used': 1}})
        else:
            msg['msg'] = "You have already used your action/bonus action for this turn."

    if rdy_to_attack:
        broadcast_value = True
        # Attack roll.
        attack_status = attacks.attack_roll(actor, targets[0], weapon, weapon_property,
                                            chars_distance)
        # If actor hits the target.
        if attack_status == 'success' or attack_status == 'critical':
            # Damage roll variable
            if attack_status == 'critical':
                critical = True
                msg['msg'] = actor['name'] + " succeeded to critically hit " + target['name'] + " with his attack."
            else:
                msg['msg'] = actor['name'] + " succeeded to hit " + target['name'] + " with his attack."

            # Damage roll.
            damage_result = attacks.damage_roll(actor, targets[0], weapon, weapon_property,
                                                critical, bonus_action_attack)

            # Update monster's hit points.
            return_msg = apply_damage(damage_result, ObjectId(session['game_id']), targets[0],
                            weapon['damage_type'])
            
            # Merge two dictionaries.
            msg.update(return_msg)
        else:
            msg['msg'] = actor['name'] + " missed to hit " + target['name'] + " with his attack."

        # Check which action type to update.
        if data['action_type'] == 'action':
            update_obj = {'character_documents.$.actions_used': 1}
        elif data['action_type'] == 'bonus_action':
            update_obj = {'character_documents.$.bonus_actions_used': 1}

        # Update actor's action/bonus action status.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id']),
            'character_documents.combat_identifier': actor['combat_identifier']},
            {'$inc': update_obj})

        if data['action_type'] == 'action':
            # Update actor's attack points.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': {'character_documents.$.attack_points': -weapon['attack_points']}})

        # Update actor's weapon used.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id']),
            'character_documents.combat_identifier': actor['combat_identifier']},
            {'$set': {'character_documents.$.weapon_used': weapon['name']}})
    elif rdy_to_cast_spell:
        if 'armor_proficiency_lack' not in actor['debuffs']['spellcasting']:
            params = [session['game_id'], actor]
            reply_msg = None

            # Check if spell is selfcasted. If not, send the targets as a parameter.
            if spell['range'] > 0:
                params.append(targets)

            # If the spell has a temporary aspect pass the time.
            if 'traits' in spell:
                if 'expires' in spell['traits']:
                    params.append(combat_document['time'])

            # If the spell has subspells, pass the one selected from the data.
            if 'subspells' in spell:
                params.append(subspell)

            targets_names = ""
            for target in targets:
                targets_names += target['combat_identifier']

                if target != targets[-1]:
                    targets_names += ", "

            msg['msg'] = actor['combat_identifier'] + " casted " + spell['name']

            if targets_names:
                msg['msg'] += " to " + targets_names

            if spell['type'] != 'utility' and spell['type'] != 'creation':
                reply_msg = getattr(spells, spell['name'])(*params)

            # Merge two dictionaries.
            if reply_msg:
                if 'msg' in reply_msg:
                    msg['msg'] += reply_msg['msg']
                else:
                    msg.update(reply_msg)
            
            # Broadcast spell cast.
            broadcast_value = True

            # Check which action type to update.
            if data['action_type'] == 'action':
                update_obj = {'character_documents.$.actions_used': 1}
            elif data['action_type'] == 'bonus_action':
                update_obj = {'character_documents.$.bonus_actions_used': 1}

            # Update actor's action/bonus action status.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': update_obj})

            # Update actor's spell casted.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$set': {'character_documents.$.previous_casted_spell': spell['name']}})

            # List the spell as burned, if it needs short/long rest for re-use.
            if 'needs_rest' in spell:
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$addToSet': {'character_documents.$.burned_spells_abilities': spell['name']}})

            # Update actor's spell slots, only if spell is not a cantrip.
            if spell['level'] > 0:
                actor['spell_slots_used'][spell['level'] - 1] += 1
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                    'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$set': {'character_documents.$.spell_slots_used': actor['spell_slots_used']}})
        else:
            msg['msg'] = "You cannot cast a spell wearing armor that you lack proficiency with."
    elif rdy_to_use_ability:
        # Base parameters for every ability.
        params = [actor, session['game_id'], combat_document['time']]

        # Additional parameters for specific abilities.
        if subability:
            # Pass the targets.
            params.append(targets)

            # Pass the name of the sub-ability selected.
            params.append(subability['name'])

        # Call the function with the same name as the ability selected.
        reply_msg = getattr(spells, ability['name'])(*params)

        msg['msg'] = actor['combat_identifier'] + " is casting " + ability['name']
        if subability:
            targets_names = ""
            for target in targets:
                targets_names += target['combat_identifier']

                if target != targets[-1]:
                    targets_names += ", "
            
            msg['msg'] += " - " + subability['name'] + " to " + targets_names

        broadcast_value = True

        # Merge two dictionaries.
        if reply_msg:
            msg.update(reply_msg)

        # Check which action type to update.
        if ability['action_used'] == 'action':
            update_obj = {'character_documents.$.actions_used': 1}
        elif ability['action_used'] == 'bonus_action':
            update_obj = {'character_documents.$.bonus_actions_used': 1}
        elif ability['action_used'] == 'no_action':
            update_action = False

        # Update actor's action/bonus action status.
        if update_action:
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': update_obj})

        # List the ability as burned, if it needs short/long rest for re-use.
        if 'rest' in ability:
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$addToSet': {'character_documents.$.burned_spells_abilities': ability['name']}})

    emit("message", msg, broadcast=broadcast_value, namespace='/combat_page_namespace')

if __name__ == "__main__":
    # Retrieve port number from enviroment or set to 5000, by default.
    port = int(environ.get("PORT", 5000))

    socketio.run(app, host='0.0.0.0', port=port)
