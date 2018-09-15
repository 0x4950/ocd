@app.route('/game/<game_id_url>/')
@flask_login.login_required
def game_page(game_id_url):
    players = []
    players_character = None

    # Search if the game exists in the games collection.
    if ObjectId.is_valid(game_id_url):
        # Check if the game exists.
        if gamesCollection.find_one({'_id': ObjectId(game_id_url)}):
            game = gamesCollection.find_one({'_id': ObjectId(game_id_url)})

            if belonger(game_id_url):
                # Retrieve DM's username.
                dm_username = usersCollection.find_one(
                    {'_id': game['dm_id']}, {'_id': 0, 'username': 1})

                # Pull players info from the users collection.
                for player in game['players']:
                    player_dict = {}
                    player_dict['username'] = usersCollection.find_one(
                        {'_id': ObjectId(player['_id'])})['username']

                    if player['character']:
                        player_dict['character'] = characters_collection.find_one(
                            {'_id': ObjectId(player['character'])})
                    else:
                        player_dict['character'] = None

                    if player_dict['username'] == flask_login.current_user.id:
                        players_character = player_dict['character']

                    players.append(player_dict)

                return render_template('gamePage.html', game_id=game, players=players,
                                       dm_username=dm_username,
                                       players_character=players_character)
            else:
                flash(u'You do not participate in this game')
        else:
            flash(u'This game does not exist.')
    else:
        flash(u'This game does not exist')
    return redirect(url_for('dashboard'))