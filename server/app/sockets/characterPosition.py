@socketio.on('character_position', namespace='/combat_page_namespace')
def character_position(character_position_info):
    distance = 0
    message = {'msg': None}

    character_identifier = character_position_info['character_identifier']
    new_position = character_position_info['character_position']

    # Retrieve character/monster document.
    character_document = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id']),
         'character_documents.combat_identifier': character_identifier},
        {'_id': 0, 'character_documents.$': 1})['character_documents'][0]

    # Retrieve occupied positions as a list.
    occupied_positions = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])},
        {'_id': 0, 'positions_occupied': 1})['positions_occupied']

    old_position = character_document['position']

    if new_position != old_position:
        if character_document['health_status'] == 'alive':
            # If position is not already occupied by another character/monster.
            if new_position not in occupied_positions:
                # If the position coming from the page is valid.
                if new_position in range(0, 64):
                    # Calculate distance character want to travel.
                    if old_position is not None:
                        distance = euclidean_distance(old_position, new_position)

                    if distance <= character_document['displacement_left']:
                        if old_position in occupied_positions:
                            occupied_positions.remove(old_position)
                        occupied_positions.append(new_position)

                        character_documents = combat_session_monsters_collection.find_one_and_update(
                            {'game_id': ObjectId(session['game_id']),
                            'character_documents.combat_identifier': character_identifier},
                            {'$set': {'positions_occupied': occupied_positions,
                                    'character_documents.$.position': new_position},
                            '$inc': {'character_documents.$.displacement_left': -distance}},
                            {'_id': 0, 'character_documents': 1, },
                            return_document=ReturnDocument.AFTER)['character_documents']

                        for character in character_documents:
                            if character['combat_identifier'] == character_identifier:
                                character_document = character

                        # Load old position to sent to client.
                        character_document['old_position'] = old_position

                        # Delete '_id' field from player characters.
                        if '_id' in character_document:
                            del character_document['_id']

                        emit("display_loaded_" + character_document['type'], character_document, broadcast=True)
                    else:
                        message['msg'] = "You are not fast enough to move to that position."
                else:
                    message['msg'] = "That location is out of bounds."
            else:
                message['msg'] = "That position is already occupied."
        else:
            message['msg'] = "You cannot move in your condition."

        emit("message", message)