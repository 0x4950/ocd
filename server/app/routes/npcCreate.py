@app.route('/game/<game_id_url>/npc_creation', methods=['GET', 'POST'])
@flask_login.login_required
def npc_creation(game_id_url):
    # Initialise NPC Creation form
    npc_creation_form = NPCCreation(csrf_enabled=False)

    # If the form validates.
    if npc_creation_form.validate_on_submit():
        # Insert new NPC into database
        npcsCollection.insert_one({'npc_name': npc_creation_form.npc_name.data,
                                   'npc_description': npc_creation_form.npc_description.data,
                                   'ability_scores': npc_creation_form.npc_ability_scores.data,
                                   'game_id': ObjectId(game_id_url)})
        # Return to game page
        return redirect(url_for('npc_creation', game_id_url=game_id_url))

    npcs_list = npcsCollection.find({'game_id': ObjectId(game_id_url)})

    return render_template('npc_creation.html', npc_creation_form=npc_creation_form,
                           npcs_list=npcs_list, game_id=game_id_url)