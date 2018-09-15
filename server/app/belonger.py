def belonger(game_id):
    """
    Check if player participates in the game with the 'game_id' provided.
    Return True if he participates, False if he does not.
    """
    if usersCollection.find_one(
            {'$and': [{'username': flask_login.current_user.id},
                      {'participatingGames': {'$in': [game_id]}}]}):
        return True
    return False