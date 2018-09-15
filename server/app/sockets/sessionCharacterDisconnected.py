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