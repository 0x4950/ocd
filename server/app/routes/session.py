@app.route('/game/<game_id_url>/session/')
@flask_login.login_required
def session_page(game_id_url):
    npcs = []
    dm_username = False
    users_player = None
    game = None

    if ObjectId.is_valid(game_id_url):  # If game id is valid
        # Retrieve game document from the database.
        game = gamesCollection.find_one({'_id': ObjectId(game_id_url)})

    if game:  # If the game is found
        if belonger(game_id_url):  # Check if player participates in this game
            # If the user is the dm let the template know.
            game_dm_name = usersCollection.find_one(
                {'_id': game['dm_id']}, {'username': 1})['username']

            if game_dm_name == flask_login.current_user.id:
                dm_username = True
                # Set the field 'status' to online, so players can join the game.
                gamesCollection.update_one({'_id': game['_id']}, {"$set": {"status": 'online'}})

            if game['status'] == 'online' or dm_username is True:
                for player in game['players']:  # For each player retrieve characters
                    if player['character']:
                        # Get character from characters collection
                        char = characters_collection.find_one({'_id': player['character']})

                        # Check if the character exists.
                        if char:
                            # If character belongs to logged user inform the template
                            if char['player_name'] == flask_login.current_user.id:
                                users_player = char['name']
                                session['users_player'] = char['name']

                # Get online players from the database.
                characters = gamesCollection.find_one({'_id': game['_id']},
                                                      {'online_players': 1})['online_players']

                # Load NPCS from the database.
                for npc in npcsCollection.find({'game_id': game['_id']},
                                               {'_id': 0, 'npc_name': 1, 'npc_description': 1}):
                    npcs.append(npc)

                # Save variables to session.
                session['game_id'] = game_id_url

                return render_template('session_page.html', game=game, dm_username=dm_username, characters=characters,
                                       npcs=npcs, users_player=users_player)
            else:
                flash(u'This session is offline.')
                return redirect(url_for('game_page', game_id_url=game_id_url))
        flash(u'You do not participate in this game.')
        return redirect(url_for('dashboard'))
    flash(u'This game does not exist.')
    return redirect(url_for('dashboard'))