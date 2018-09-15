def turns_n_rounds(game_id, initiative_order):
    # Initialise the structures for handling turns and rounds and saves them to the database.
    combat_session_monsters_collection.update_one(
        {'game_id': game_id},
        {'$set': {'round': 1, 'turn': 0, 'round_length': len(initiative_order)}})