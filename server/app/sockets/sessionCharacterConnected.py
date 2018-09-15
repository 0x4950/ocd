@socketio.on('connect', namespace='/session_page_namespace')
def session_character_connected():
    # Join the room.
    join_room(session['game_id'])

    if 'users_player' in session and session['users_player']:
        # Insert player's character into 'online_players' list
        # and return the updated document.
        game = gamesCollection.find_one_and_update(
            {'_id': ObjectId(session['game_id'])},
            {"$addToSet": {"online_players": session['users_player']}},
            return_document=ReturnDocument.AFTER)

        emit('joined_player', {'characters': game['online_players']}, room=session['game_id'],
             broadcast=True)