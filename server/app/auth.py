from flask_login import LoginManager, UserMixin
from bson import ObjectId
from app import app, mongo

usersCollection = mongo.db.users

# Instantiating the Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
  def __init__(self, username=None, id=None):
    self.username = username
    self.id = id

  def get_by_username_w_password(self, username):
    try:
      dbUser = usersCollection.find_one({'username': username})

      if dbUser:
        self.username = dbUser['username']
        self.password = dbUser['password']
        self.id = str(dbUser['_id'])
        return self
      else:
          return None
    except:
      return None

  def get_by_id(self, id):
    
    dbUser = usersCollection.find_one({'_id': ObjectId(id)})

    if dbUser:
      self.username = dbUser['username']
      self.id = str(dbUser['_id'])
      return self
    else:
      return None

@login_manager.user_loader
def user_loader(id):
  if id is None:
	  redirect('/login')

  user = User()
  user.get_by_id(id)
  return user