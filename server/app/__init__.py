from flask import Flask
from flask_pymongo import PyMongo
from flask_assets import Bundle, Environment
# from flask_socketio import SocketIO

app = Flask(__name__)

# Connect to the socket.
# socketio = SocketIO(app)

# Register JS bundles as assets.
bundles = {
  'create_character_js': Bundle('dist/character-create.js', output='dist/create_character.js'),
  'dashboard_js': Bundle('dist/dashboard.js', output='dist/dashboard.js')
}
assets = Environment(app)
assets.register(bundles)

app.config["SECRET_KEY"] = 'dev-secret'

# Connect to the database.
app.config["MONGO_URI"] = 'mongodb://heroku_t67kkwpk:ucevqbvtnnv7lr2bl0sc33ov6d@ds011664.mlab.com:11664/heroku_t67kkwpk'
mongo = PyMongo(app)

# Import routes.
from app.routes import login
from app.routes import createAccount
from app.routes import dashboard
from app.routes import logout
from app.routes import campaign