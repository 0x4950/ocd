@socketio.on('monster_loaded', namespace='/combat_page_namespace')
def load_monster(monster_loaded):
    # Retrieve monster information from database
    monster_stat_block = monsters_collection.find_one(
        {'name': monster_loaded['name'].lower().replace(" ", "_")}, {'_id': 0})

    # Set unique identifiers for each monster
    monsters = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])},
        {'character_documents': 1})['character_documents']

    monster_stat_block['combat_identifier'] = gen_combat_id(monster_stat_block['name'],
                                                            len(monsters))

    # If position is not already occupied by another monster.
    if not combat_session_monsters_collection.find_one(
            {'game_id': ObjectId(session['game_id']),
             'positions_occupied': {'$in': [monster_loaded['position']]}}):
        # If the position coming from the page is valid.
        if monster_loaded['position'] in range(0, 64):
            monster_stat_block['type'] = 'monster'
            monster_stat_block['health_status'] = 'alive'
            monster_stat_block['position'] = monster_loaded['position']
            monster_stat_block['displacement_left'] = monster_stat_block['speed']
            monster_stat_block['current_hit_points'] = monster_stat_block['hit_points']
            monster_stat_block['maximum_hit_points'] = monster_stat_block['current_hit_points']
            monster_stat_block['attack_points'] = monster_stat_block['attack_points_per_turn']
            monster_stat_block['actions_used'] = 0
            monster_stat_block['displayed_hp_status'] = 'Undamaged'
            monster_stat_block['weapon_used'] = None

            # Push monster to combat session monsters database
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id'])},
                {'$push': {'character_documents': monster_stat_block,
                           'positions_occupied': monster_loaded['position']}})

            emit("display_loaded_monster", monster_stat_block, broadcast=True)

        else:
            # TODO
            # Error code for invalid position.
            pass
    else:
        # TODO
        # Complete with error message for the DM to know what went wrong.
        pass