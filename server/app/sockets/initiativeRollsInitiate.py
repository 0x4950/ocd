@socketio.on('initiate_initiative_rolls', namespace='/combat_page_namespace')
def initiate_initiative_rolls():
    rolls = dict()

    # Retrieve document from the database.
    combat_document = combat_session_monsters_collection.find_one(
        {'game_id': ObjectId(session['game_id'])})

    # Roll a dice for each character/monster.
    for character in combat_document['character_documents']:
        rolls[character['combat_identifier']] = roll_initiative(character)

    # Sort by values and save to list
    initiative_order = sorted(rolls, key=rolls.get)
    initiative_order.reverse()

    # Check whether the playing entity is either a "Character" or a "Monster".
    for character in combat_document['character_documents']:
        if character['combat_identifier'] == initiative_order[0]:
            currently_playing_is = character['type']

    # Push initiative order variables into the database document.
    combat_session_monsters_collection.update_one(
        {'game_id': ObjectId(session['game_id'])},
        {'$set': {'initiative_order': initiative_order,
                  'currently_playing_character': initiative_order[0],
                  'currently_playing_is': currently_playing_is}})

    # Initialise turns & rounds.
    turns_n_rounds(ObjectId(session['game_id']), initiative_order)

    # Push the Initiative Order to the users.
    emit('display_initiative_order', {'initiative_order': initiative_order,
                                      'currently_playing_character': initiative_order[0],
                                      'currently_playing_is': currently_playing_is,
                                      'round': 1}, broadcast=True)