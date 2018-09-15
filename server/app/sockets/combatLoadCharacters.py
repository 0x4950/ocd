@socketio.on('load_combat_characters', namespace='/session_page_namespace')
def load_combat_characters(characters_selected):
    character_document = None
    msg = dict()

    if not combat_session_monsters_collection.find_one({'game_id': ObjectId(session['game_id'])}):
        combat_session_monsters_collection.insert_one(
            {'game_id': ObjectId(session['game_id']),
             'online_combat_characters': [], 'character_documents': [],
             'combat_characters': [],
             'time': 0,
             'round': 0,
             'currently_playing_character': None,
             'currently_playing_is': None,
             'initiative_order': None,
             'positions_occupied': []})

        for counter, character in enumerate(characters_selected):
            # Load the character document from the database.
            character_document = characters_collection.find_one({'name': character})

            if character_document:
                # Initialize values needed for combat.
                character_document['combat_identifier'] = gen_combat_id(character_document['name'],
                                                                        counter)
                character_document['displacement_left'] = character_document['speed']
                character_document['position'] = None
                character_document['previous_casted_spell'] = None
                character_document['weapon_used'] = None
                character_document['spell_used'] = None
                character_document['attack_points'] = character_document['attack_points_per_turn']
                character_document['actions_used'] = 0
                character_document['bonus_actions_used'] = 0
                character_document['rest_status'] = "unrested"

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id'])},
                    {'$push': {'character_documents': character_document}})

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id'])},
                    {'$push': {'combat_characters': character_document['combat_identifier']}})

    # Message to redirect users to combat session page.
    msg['type'] = "enter_combat"
    msg['combat_characters'] = characters_selected
    emit('message', msg, broadcast=True)