@app.route('/game/<game_id_url>/exit_combat/')
@flask_login.login_required
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