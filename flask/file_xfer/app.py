#!/usr/bin/env python3

# Two stage upload - form then upload pages
# Attempt to add WTF Flask functionality
# Basic flask upload handler from blueimp jQuery File Upload

import os,re,urllib.parse

from flask import Flask,current_app,json,request,render_template,flash,\
   redirect,url_for
from werkzeug import secure_filename

from flask_wtf import Form
from wtforms import StringField
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3ybR~XHH!jmN]LWX/,?RT'

class UploadForm(Form):
    name = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email Address', [validators.Length(min=6, max=35)])
    id = TextField('Analysis ID', [validators.Length(min=1, max=25)])

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

    with open(path,mode) as destination:
        destination.write(f.read())

@app.route('/')
def root_page():
    return redirect(url_for('upload'))

@app.route('/uploadfile',methods=['POST'])
def upload_file():
    recvd=request.files['files[]']
    last=True
    mode="wb"

    if 'Content-Range' in request.headers:
       range=re.split('[ -/]',request.headers['Content-Range'])
       if range[1]!='0':
          mode="ab"
       if int(range[2])+1<int(range[3]):
          last=False

    save_upload(recvd,mode,
       os.path.join("frobozz",secure_filename(recvd.filename)))

    if last==True:
       params=urllib.parse.parse_qs(request.form['data'])
       print("params",params)
  
    return make_response(200,{"success":True})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form=UploadForm(request.form)
    if request.method == 'POST' and form.validate():
        #print("form ok!",[form.name.data,form.email.data,form.id.data])
        data={"name":form.name.data,"email":form.email.data,"id":form.id.data}
        return render_template('uploadfile.html',
           data=urllib.parse.urlencode(data))

    return render_template('uploadform.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
