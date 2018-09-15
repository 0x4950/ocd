@app.route('/game/<game_id_url>/createCharacter', methods=['GET', 'POST'])
@flask_login.login_required
def character_creation_page(game_id_url):
    error = None
    character_creation_form = CharacterCreationForm()

    if character_creation_form.validate_on_submit():
        try:
            # Call creator from genesis and initialize character.
            character_object = creator(character_creation_form,
                                       flask_login.current_user.id, game_id_url)

            # Encoder options.
            set_encoder_options('json', sort_keys=True, indent=2)

            # Encode Character object - Turn the object dictionary into a string.
            character_string = encode(character_object, unpicklable=False)

            # Recreate a Python object from a JSON str.
            character_json = decode(character_string)

            # Insert into the database.
            characters_collection.replace_one(
                {'game_id': game_id_url, 'player_name': flask_login.current_user.id},
                character_json, upsert=True)

            # Encode Character object - Turn the object dictionary into a string.
            character_object_json = json.loads(encode(character_object))

            # Insert into the database.
            character_python_objects_collection.replace_one(
                {'game_id': game_id_url, 'player_name': flask_login.current_user.id},
                character_object_json, upsert=True)

            # Find the id of the logged in player.
            user_id = usersCollection.find_one(
                {'username': flask_login.current_user.id}, {'_id': 1})

            ver = characters_collection.find_one(
                {'game_id': game_id_url, 'player_name': flask_login.current_user.id},
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

    return render_template('character_creation.html',
                           character_creation_form=character_creation_form, classes=classes, error=error)
