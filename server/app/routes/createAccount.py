from app import app

@app.route('/create_account/', methods=['GET', 'POST'])
def create_account():
  if not usersCollection.find_one({'username': form.username.data}):
    hashed_password = generate_password_hash(form.password.data)
    usersCollection.insert({
      'username': form.username.data,
      'password': hashed_password,
      'participatingGames': []
    })
    flash(u'Account successfully created')
    return redirect(url_for('login'))
  else:
    flash(u'The username you have chosen is already in use.', 'used_username')
  return render_template('create_account.html')