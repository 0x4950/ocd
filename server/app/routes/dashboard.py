from app import app
from flask_login import login_required
from flask import render_template

@app.route("/dashboard/", methods=['GET'])
@login_required
def dashboard():
  return render_template('dashboard.html')