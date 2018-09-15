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