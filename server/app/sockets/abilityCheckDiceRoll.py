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
                     'player_name': flask_login.current_user.id}):
                result = dice_rolling(char['name'], char['skill'])

                log_msg['character'] = char['name']
                log_msg['skill'] = char['skill']

                log_msg['result'] = result
            else:
                log_msg['opponent'] = char['name']

    emit("message", log_msg, broadcast=True)