"""
This script runs the FlaskTemplateVS2015 application using a development server.
"""

from os import environ
from FlaskTemplateVS2015 import app

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
