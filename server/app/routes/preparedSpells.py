@app.route('/game/<game_id_url>/prepared_spells', methods=['GET', 'POST'])
@flask_login.login_required
def prepared_spells(game_id_url):
    character_document = None
    selected_spells = set()
    spells_list = []
    spell_level_cap = 0
    error = None

    # Check if character belongs to the game.
    if belonger(game_id_url):
        # TODO Check if character has spells.

        # Retrive character document from the database.
        character_document = characters_collection.find_one(
            {'game_id': game_id_url, 'player_name': flask_login.current_user.id})

        if request.method == 'POST':
            # Get all the checked spells.
            for item in request.form:
                selected_spells.add(item)

            try:
                # Call function to set the prepared spells.
                result = spells.set_prepared_spells(character_document, selected_spells)
                characters_collection.update_one(
                    {'name': character_document['name']},
                    {'$set': {'prepared_spells': list(result)}})
                return redirect(url_for('game_page', game_id_url=game_id_url))
            except spells.PrepareSpellException as e:
                error = e.args[0]
                flash(error)

        # Retrieve all spells the database.
        if character_document['level'] >= 5:
            spell_level_cap = 3
        elif character_document['level'] >= 3:
            spell_level_cap = 2
        else:
            spell_level_cap = 1

        for spell in spells_collection.find(
                {'$and': [{'level': {'$lte': spell_level_cap},
                          'class': {'$in': [character_document['class']]}}]}):
            spells_list.append(spell)

        return render_template('prepared_spells.html', game_id_url=game_id_url,
                               character=character_document, spells=spells_list, error=error)
    else:
        flash("You do not participate in this game.")

    return redirect(url_for('dashboard'))