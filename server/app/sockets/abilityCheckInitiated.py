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