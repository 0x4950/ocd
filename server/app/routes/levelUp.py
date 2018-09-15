@app.route('/game/<game_id_url>/level_up', methods=['GET', 'POST'])
@flask_login.login_required
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
            {'game_id': game_id_url, 'player_name': flask_login.current_user.id})

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
                'player_name': flask_login.current_user.id,
                'name': character_document['name']})

            # Save the document id, so it can be replaced later.
            character_object_document_id = character_python_object['_id']
            del character_python_object['_id']

            # Turn the dictionary into a string.
            character_python_object = json.dumps(character_python_object)

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