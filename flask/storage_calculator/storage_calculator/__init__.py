from flask import Flask, session, g
from flask.ext.login import LoginManager
login_manager = LoginManager()
app = Flask(__name__)
app.config.from_object('storage_calculator.default_settings')
login_manager.setup_app(app)

import storage_calculator.views
login_manager.login_view = "login"
#app.config.from_envvar('STORAGE_CALCULATOR_SETTINGS')


from authentication import User
@login_manager.user_loader
def load_user(userid):
    if session["user_id"] and g:
        g.username = '{0}@{1}'.format(session["user_id"], app.config['DOMAIN'])
    return User.get(userid)


__version__ = '0.1.0'

if __name__ == 'main': app.run()
