from app import app, mongo
from bson import ObjectId
from flask_login import login_required, current_user
from flask import render_template, request, abort, jsonify

usersCollection = mongo.db.users
gamesCollection = mongo.db.games

@app.route("/dashboard/", methods=['GET'])
@login_required
def dashboard():
  return render_template('dashboard.html')

@app.route('/api/campaings/', methods=['GET', 'POST'])
@login_required
def campaings():
  if request.method == "POST":
    # User made post request to create a new campaign.
    newCampName = request.json['name']
    # Check that the player does not participate in a campaign with the name provided.    
    name_conflict = gamesCollection.find_one({'$and':[{'name': newCampName},
    {'$or':[{'dm_id': current_user.id}, {'players.pid': current_user.id}]}]})

    if not name_conflict:
      # Insert the game document into 'gamesCollection' with info provided.
      game_id = gamesCollection.insert_one({
        'name': newCampName,
        'dm_id': current_user.id,
        'players': [],
        'staus': 'offline',
        'online_players': []
      })

      # Updating DM's participating games list with new game.
      usersCollection.update(
        {'username': current_user.username},
        {'$push': {'participatingGames': str(game_id.inserted_id)}})
    else:
      # Let user know that he can only participate in one campaign with a specific name.
      return abort(409)
  
  # Handle GET requests, or update the list with the new created game.
  games = []
  games_ids = usersCollection.find_one({'username': current_user.username})['participatingGames']

  for game_id in games_ids:
    game_dict = {}
    game_document = gamesCollection.find_one({'_id': ObjectId(game_id)})
    game_dict['name'] = game_document['name']
    game_dict['id'] = str(game_document['_id'])
    game_dict['created_time'] = game_document['_id'].generation_time
    games.append(game_dict)

  return jsonify(games)