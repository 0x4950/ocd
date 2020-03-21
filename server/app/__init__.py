from flask import Flask
from flask_pymongo import PyMongo
from flask_assets import Bundle, Environment
# from flask_socketio import SocketIO

# Run with 'export FLASK_APP=react-ocd.py 
#           export FLASK_ENV=development 
#           flask run --host=0.0.0.0'.
app = Flask(__name__)

app.config.from_object('config.DevelopmentConfig')

# Connect to the socket.
# socketio = SocketIO(app)

# Register JS bundles as assets.
bundles = {
  'create_character_js': Bundle('dist/character-create.js', output='dist/create_character.js'),
  'dashboard_js': Bundle('dist/dashboard.js', output='dist/dashboard.js')
}
assets = Environment(app)
assets.register(bundles)

# Connect to the database.
mongo = PyMongo(app)

# Import routes.
from app.routes import login
from app.routes import createAccount
from app.routes import dashboard
from app.routes import logout
from app.routes import campaign
from app.routes import session
from app.routes import preparedWeapons
from app.routes import combat

# Import API routes.
from app.api import getLoggedUser
from app.api import getCampaigns
