@socketio.on('next_turn', namespace='/combat_page_namespace')
def next_turn(data):
    # Increase the 'turn' counter and the time and then load the updated document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$inc': {'turn': 1, 'time': 6}},
        return_document=ReturnDocument.AFTER)

    # Check if the end of a turn has arrived.
    if combat_document['turn'] >= combat_document['round_length']:
        # Set the turn to zero again.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id'])}, {'$set': {'turn': 0}})

        # Increase the round counter.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id'])}, {'$inc': {'round': 1}})

        for character in combat_document['character_documents']:
            if character['health_status'] == 'alive' or character['health_status'] == 'unconscious':
                # Reset values for attacks, spells, movement for each character/monster.
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': character['combat_identifier']},
                    {'$set': {'character_documents.$.displacement_left': character['speed'],
                              'character_documents.$.attack_points': character['attack_points_per_turn'],
                              'character_documents.$.actions_used': 0,
                              'character_documents.$.bonus_actions_used': 0,
                              'character_documents.$.previous_casted_spell': None,
                              'character_documents.$.weapon_used': None,
                              'character_documents.$.spell_used': None}})

                # Pull temporary buffs that have expired.
                if 'buffs' in character:
                    if 'temporary' in character['buffs']:
                        for key in character['buffs']['temporary']:
                            for buff in character['buffs']['temporary'][key]:
                                if buff['expires'] < combat_document['time']:
                                    character['buffs']['temporary'][key].remove(buff)

                # Update character's document with updated buffs dictionary.
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': character['combat_identifier']},
                    {'$set': {'character_documents.$.buffs': character['buffs']}})

                # Check for overtime damage effects that have expired.
                for debuff in character['debuffs']['overtime_effects']:
                    if debuff['type'] == 'damage' and debuff['expires'] < combat_document['time']:
                        apply_damage(debuff['amount'], ObjectId(session['game_id']),
                                     character, debuff['damage_type'])

                        # If the debuff expires on use remove it from the debuffs list.
                        if debuff['expires_on_use']:
                            combat_session_monsters_collection.update_one(
                                {'game_id': ObjectId(session['game_id']),
                                 'character_documents.combat_identifier': character['combat_identifier']},
                                {'$pull': {'character_documents.$.debuffs.overtime_effects': debuff}})

        # Retrieve the updated document
        combat_document = combat_session_monsters_collection.find_one(
            {'game_id': ObjectId(session['game_id'])})

    # Change 'currently_playing_character' saved in the database and reload the document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'currently_playing_character': combat_document['initiative_order'][combat_document['turn']]}},
        return_document=ReturnDocument.AFTER)

    # Check whether the playing entity is either a "Character" or a "Monster".
    currently_playing_is = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id']),
         'character_documents.combat_identifier': combat_document['currently_playing_character']},
        {'_id': 0, 'character_documents.$.type': 1})['character_documents'][0]['type']

    # Change 'currently_character_is' saved in the database and reload the document.
    combat_document = combat_session_monsters_collection.find_one_and_update(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'currently_playing_is': currently_playing_is}},
        return_document=ReturnDocument.AFTER)

    emit('changing_turn', {'currently_playing_character': combat_document['currently_playing_character'],
                           'currently_playing_is': combat_document['currently_playing_is'],
                           'time': combat_document['time'], 'round': combat_document['round']},
                           broadcast=True)