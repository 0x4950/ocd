@socketio.on('server_rest', namespace='/session_page_namespace')
def server_rest(characters_list):
    rest_msg = {}

    for character in characters_list:
        character_document = characters_collection.find_one(
            {'game_id': session['game_id'], 'name': character})

        maximum_character_hit_points = character_document['maximum_hit_points']

        # See if character has maximum hit points buff.
        if 'maximum_hit_points' in character_document['buffs']['temporary']:
            for buff in character_document['buffs']['temporary']['maximum_hit_points']:
                # Increase maximum hit points of the character by the buff amount.
                maximum_character_hit_points += buff['amount']

        characters_collection.update_one(
            {'game_id': session['game_id'], 'name': character},
            {"$set": {"rest_status": "rested",
                      "death_saving_throws_attempts": [0, 0],
                      "burned_spells_abilities": [],
                      "spell_slots_used": [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      "current_hit_points": maximum_character_hit_points}})

        characters_collection.update_one(
            {"$or": [{ "health_status": "stable"}, {"health_status": "unconscious"}]},
            {"$set": {"health_status": "alive"}})

        rest_msg['type'] = 'rest'
        rest_msg['rested_characters'] = characters_list

        emit('message', rest_msg, broadcast=True)