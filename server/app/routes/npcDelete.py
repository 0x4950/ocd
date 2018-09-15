@app.route('/game/<game_id_url>/delete_npc/', methods=['GET'])
@flask_login.login_required
def delete_npc(game_id_url):
    npc_name = request.args.get('npc_name')

    npcsCollection.delete_one({'game_id': ObjectId(game_id_url), 'npc_name': npc_name})

    return redirect(url_for('npc_creation', game_id_url=game_id_url))