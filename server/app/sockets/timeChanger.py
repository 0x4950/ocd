@socketio.on('time_changer', namespace='/session_page_namespace')
def time_changer(current_time):
    # Save the time to the database.
    gamesCollection.update_one(
        {'_id': ObjectId(session['game_id'])}, {'$set': {'time': current_time}})

    # Simply retransmit the selected time to all clients.
    emit('update_time', current_time, broadcast=True)