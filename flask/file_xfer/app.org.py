#!/usr/bin/env python3

# Basic flask upload handler from blueimp jQuery File Upload

import os

from flask import Flask,current_app,json,request
from werkzeug import secure_filename

app = Flask(__name__)

def make_response(status=200, content=None):
    """ Construct a response to an upload request.
    Success is indicated by a status of 200 and { "success": true }
    contained in the content.

    Also, content-type is text/plain by default since IE9 and below chokes
    on application/json. For CORS environments and IE9 and below, the
    content-type needs to be text/html.
    """
    return current_app.response_class(json.dumps(content,
        indent=None if request.is_xhr else 2), mimetype='text/plain')

def save_upload(f,mode,path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    #with open(path, 'wb+') as destination:
    with open(path,mode) as destination:
        destination.write(f.read())

@app.route('/')
def hello_world():
    return 'File upload test app'

@app.route('/upload/',methods=['POST'])
def upload_handler():
    print("request.form?",request.form)
    if 'name' in request.form:
       print("name?",request.form['name'])
    if 'email' in request.form:
       print("email?",request.form['email'])
    if 'analysis_id' in request.form:
       print("analysis id?",request.form['analysis_id'])

    recvd=request.files['files[]']
  
    if 'Content-Range' in request.headers and \
       "bytes 0-" not in request.headers['Content-Range']:
       mode="ab"
    else: 
       mode="wb"
       
    save_upload(recvd,mode,
       os.path.join("frobozz",secure_filename(recvd.filename)))

    return make_response(200,{"success":True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
