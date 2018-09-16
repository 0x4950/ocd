from app import mongo
from flask_login import current_user

usersCollection = mongo.db.users

def belonger(game_id):
    """
    Check if player participates in the game with the 'game_id' provided.
    Return True if he participates, False if he does not.
    """
    if usersCollection.find_one(
            {'$and': [{'username': current_user.username},
                      {'participatingGames': {'$in': [game_id]}}]}):
        return True
    return False