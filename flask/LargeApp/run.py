#! /usr/bin/env python3
#launch a flask server.

from app import app
app.run(host='0.0.0.0', port=8080, debug=True)
