def check_experience_points(game_id, character_name):
    # Character advancement table.
    character_advancement_table = (300, 900, 2700, 6500)

    for i, value in enumerate(character_advancement_table):
        characters_collection.update_one(
            {'game_id': game_id,
             'name': character_name,
             'experience_points': {'$gte': value},
             'level': {'$lte': i+1}},
            {'$set': {'level_up_ready': True},
             '$inc': {'levels_gained': 1}})

        character_python_objects_collection.update_one(
            {'game_id': game_id,
             'name': character_name,
             'experience_points': {'$gte': value},
             'level': {'$lte': i+1}},
            {'$set': {'level_up_ready': True},
             '$inc': {'levels_gained': 1}})

        if i == 2:
            characters_collection.update_one(
                {'game_id': game_id,
                 'name': character_name,
                 'experience_points': {'$gte': value},
                 'asi_used': False},
                {'$inc': {'ability_score_points': 2}})

            character_python_objects_collection.update_one(
                {'game_id': game_id,
                 'name': character_name,
                 'experience_points': {'$gte': value},
                 'asi_used': False},
                {'$inc': {'ability_score_points': 2}})