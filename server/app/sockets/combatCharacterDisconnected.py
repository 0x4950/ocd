@socketio.on('disconnect', namespace='/combat_page_namespace')
def combat_character_disconnected():
    # Leave the room.
    leave_room(session['game_id'])