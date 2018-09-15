from app import app, mongo
from app.auth import User
from flask_login import login_user, current_user
from flask import request, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash

# Save database documents to local variables.
usersCollection = mongo.db.users
gamesCollection = mongo.db.games


@app.route("/", methods=['GET', 'POST'])
def login():
  # If the user is already signed in, redirect him Dashboard.
  if current_user.is_authenticated:
    return redirect(url_for('dashboard'))

  if request.method == 'POST':
    form_username = request.form['username']
    userObj = User()
    user = userObj.get_by_username_w_password(form_username)
    if user and check_password_hash(user.password, request.form['password']):
      login_user(user)
      return redirect(url_for('dashboard'))
    else:
      flash(u'Incorrent password.', 'incorrect_password')

  return render_template('login_page.html')