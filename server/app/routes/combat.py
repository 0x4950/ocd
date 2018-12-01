from bson import ObjectId
from app import app, mongo
from app.belonger import belonger
from flask_login import login_required, current_user
from flask import flash, redirect,render_template, url_for

gamesCollection = mongo.db.games
usersCollection = mongo.db.users
charactersCollection = mongo.db.characters

@app.route('/campaign/<campaign_id>/session/combat/')
@login_required
def combat(campaign_id):
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
    if ObjectId.is_valid(campaign_id):
        # Retrieve game document from the database
        game = gamesCollection.find_one({'_id': ObjectId(campaign_id)})

    # If the game is found in the database.
    if game:
        # Check if player participates in this game
        if belonger(campaign_id):
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
                    session['game_id'] = campaign_id

                    return render_template('combat.html', campaign_id=campaign_id, user_is_dm=user_is_dm,
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
                return redirect(url_for('session_page', campaign_id=campaign_id))
        else:
            flash("You do not participate in this game.")
    else:
        flash("This game does not exist.")
    return redirect(url_for('dashboard'))