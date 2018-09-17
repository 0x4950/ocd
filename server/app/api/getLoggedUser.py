from app import app, mongo
from flask_login import login_required, current_user
from flask import jsonify

usersCollection = mongo.db.users

@app.route('/api/getLoggedUser/', methods=['GET'])
@login_required
def getLoggedUser():
  return jsonify(loggedUser=current_user.username)