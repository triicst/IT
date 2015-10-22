DEBUG = False
SESSION_COOKIE_SECURE = True # Set to True when in prod with SSL
DOMAIN = 'fhcrc.org'
BASE_DN = 'dc=fhcrc,dc=org'
LDAP_URL = 'ldaps://dc.fhcrc.org'
SECRET_KEY = '12345678901234567890' # WTF uses this to guard against CSRF
