import sys
import ldap
from storage_calculator import app
#ers from flask.ext.wtf import Form, TextField, PasswordField, validators
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators
from flask.ext.login import UserMixin

class LoginForm(Form):
    """
    Example login form adapted from snippet at: 
        http://flask.pocoo.org/snippets/64/
    """
    username = TextField('username', [validators.Required()])
    password = PasswordField('password', [validators.Required()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None


    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        la = LDAPAuth(self.username.data, self.password.data, 
            app.config['DOMAIN'], app.config['BASE_DN'], 
            app.config['LDAP_URL'])

        # For testing only, need to remove
        if self.username.data == 'guest':
            self.user = User(self.username.data, self.username.data)
            return True

        if not la.authenticate():
            self.password.errors.append('Invalid credentials, please try again')
            return False
        else:
            self.user = User(self.username.data, self.username.data)
            return True


class LDAPAuth(object):
    """
    Bind to directory service to test credentials.
    """


    def __init__(self, username, password, domain='example.com', 
        base_dn='dc=example,dc=com', ldap_url='ldap://dc.example.com'):
        self.username = username 
        self.password = password
        self.domain = domain
        self.email = '{0}@{1}'.format(username, domain)
        self.base_dn = base_dn
        self.ldap_url = ldap_url


    def authenticate(self):
        """
        Return boolean indicating credentials are sufficient (or not) for 
        binding to LDAP/AD.
        """
        try:
            sbs = ldap.initialize(self.ldap_url)
            sbs.simple_bind_s(self.email, self.password)
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        
        # Return False by default...
        return False



class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    @staticmethod
    def get(user_id):
        return User(user_id, user_id)
