@socketio.on('connect', namespace='/combat_page_namespace')
def combat_character_connected():
    # Join the room.
    join_room(session['game_id'])