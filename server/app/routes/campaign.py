from bson import ObjectId
from app import app, mongo
from app.belonger import belonger
from flask_login import login_required, current_user
from flask import flash, redirect,render_template, url_for

gamesCollection = mongo.db.games
usersCollection = mongo.db.users
charactersCollection = mongo.db.characters

@app.route('/campaign/<campaign_id>/')
@login_required
def game_page(campaign_id):
    players = []
    players_character = None

    # Search if the game exists in the games collection.
    if ObjectId.is_valid(campaign_id):
        # Check if the game exists.
        if gamesCollection.find_one({'_id': ObjectId(campaign_id)}):
            game = gamesCollection.find_one({'_id': ObjectId(campaign_id)})

            if belonger(campaign_id):
                # Retrieve DM's username.
                dm_username = usersCollection.find_one(
                    {'_id': game['dm_id']}, {'_id': 0, 'username': 1})

                # Pull players info from the users collection.
                for player in game['players']:
                    player_dict = {}
                    player_dict['username'] = usersCollection.find_one(
                        {'_id': ObjectId(player['_id'])})['username']

                    if player['character']:
                        player_dict['character'] = charactersCollection.find_one(
                            {'_id': ObjectId(player['character'])})
                    else:
                        player_dict['character'] = None

                    if player_dict['username'] == current_user.username:
                        players_character = player_dict['character']

                    players.append(player_dict)

                return render_template('campaign.html', game_id=game, players=players,
                                       dm_username=dm_username,
                                       players_character=players_character)
            else:
                flash(u'You do not participate in this game')
        else:
            flash(u'This game does not exist.')
    else:
        flash(u'This game does not exist')
    return redirect(url_for('dashboard'))