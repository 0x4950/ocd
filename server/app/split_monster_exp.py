def split_monster_exp(monster, game_id):
    character_counter = 0

    characters = combat_session_monsters_collection.find_one(
        {'game_id': game_id}, {'_id': 0, 'character_documents': 1})['character_documents']

    for character in characters:
        if (character['type'] == 'player_character') and (character['health_status'] == 'alive'):
            character_counter += 1

    exp_each = monster['experience'] / character_counter

    for character in characters:
        if (character['type'] == 'player_character') and (character['health_status'] == 'alive'):
            combat_session_monsters_collection.update_one(
                {'game_id': game_id,
                 'character_documents.combat_identifier': character['combat_identifier']},
                {'$inc': {'character_documents.$.experience_points': exp_each}})