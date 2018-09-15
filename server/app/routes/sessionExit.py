@app.route('/game/<game_id_url>/exit_session/')
@flask_login.login_required
def exit_session(game_id_url):
    # Set the game variable back to 'offline', so players cannot join.
    gamesCollection.update_one({'_id': ObjectId(game_id_url)}, {"$set": {"status": 'offline'}})
    
    # Inform joined players that the session is over.
    dc_msg = dict()
    dc_msg['type'] = 'exit_session'
    socketio.emit('message', dc_msg, broadcast=True, namespace='/session_page_namespace')

    return redirect(url_for('game_page', game_id_url=game_id_url))