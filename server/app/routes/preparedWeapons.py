@app.route('/game/<game_id_url>/prepared_weapons', methods=['GET', 'POST'])
@flask_login.login_required
def prepared_weapons(game_id_url):
    character_document = None
    selected_weapons = list()
    error = None

    # Check if character belongs to the game.
    if belonger(game_id_url):

        # Retrive character document from the database.
        character_document = characters_collection.find_one(
            {'game_id': game_id_url,
             'player_name': flask_login.current_user.id})

        if request.method == 'POST':
            request_weapons = dict(request.form)

            for item in request_weapons:
                for i in range(len(request_weapons[item])):
                    selected_weapons.append(item)

            try:
                # Call function to set the prepared weapons.
                result = attacks.set_prepared_weapons(character_document, selected_weapons)

                # Update the database.
                characters_collection.update_one(
                    {'game_id': game_id_url, 'name': character_document['name']},
                    {'$set': {'equipped': list(result)}})

                return redirect(url_for('game_page', game_id_url=game_id_url))
            except attacks.PrepareWeaponException as e:
                error = e.args[0]
                flash(error)

        return render_template('prepared_weapons.html', game_id_url=game_id_url,
                               character=character_document, spells=spells, error=error)
    else:
        flash("You do not participate in this game.")

    return redirect(url_for('dashboard'))