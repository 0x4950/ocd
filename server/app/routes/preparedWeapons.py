from app import app, mongo
from app.prepareWeapons import PrepareWeaponException, set_prepared_weapons
from app.belonger import belonger
from flask_login import login_required, current_user
from flask import flash, request, redirect,render_template, url_for

charactersCollection = mongo.db.characters

@app.route('/game/<game_id_url>/prepared_weapons', methods=['GET', 'POST'])
@login_required
def prepared_weapons(game_id_url):
    character_document = None
    selected_weapons = list()
    error = None

    # Check if character belongs to the game.
    if belonger(game_id_url):

        # Retrive character document from the database.
        character_document = charactersCollection.find_one(
            {'game_id': game_id_url,
             'player_name': current_user.username})

        if request.method == 'POST':
            request_weapons = dict(request.form)

            for item in request_weapons:
                for i in range(len(request_weapons[item])):
                    selected_weapons.append(item)

            try:
                # Call function to set the prepared weapons.
                result = set_prepared_weapons(character_document, selected_weapons)

                # Update the database.
                charactersCollection.update_one(
                    {'game_id': game_id_url, 'name': character_document['name']},
                    {'$set': {'equipped': list(result)}})

                return redirect(url_for('game_page', campaign_id=game_id_url))
            except PrepareWeaponException as e:
                error = e.args[0]
                flash(error)

        return render_template('weaponsPrepared.html', game_id_url=game_id_url,
                               character=character_document, error=error)
    else:
        flash("You do not participate in this game.")

    return redirect(url_for('dashboard'))