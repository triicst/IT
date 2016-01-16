#!/usr/bin/env python3

# Attempt to add WTF Flask functionality
# Basic flask upload handler from blueimp jQuery File Upload

import os

from flask import Flask,current_app,json,request,render_template,flash,\
   redirect,url_for
from werkzeug import secure_filename

from flask_wtf import Form
from wtforms import StringField
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3ybR~XHH!jmN]LWX/,?RT'

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.Required()])

class UploadForm(Form):
    name = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email Address', [validators.Length(min=6, max=35)])
    id = TextField('Analysis ID', [validators.Length(min=1, max=25)])

class MyForm(Form):
    name = StringField('name', validators=[DataRequired()])

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
    form=MyForm()
    #return render_template('submit.html', form=form)
    return 'File upload test app'

@app.route('/upload-old/',methods=['POST'])
def upload_handler():

    print("HERE!")
    print("form:",request.form)

    recvd=request.files['files[]']

    if 'Content-Range' in request.headers and \
       "bytes 0-" not in request.headers['Content-Range']:
       mode="ab"
    else: 
       mode="wb"
       
    save_upload(recvd,mode,
       os.path.join("frobozz",secure_filename(recvd.filename)))

    return make_response(200,{"success":True})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form=UploadForm(request.form)
    if request.method == 'POST' and form.validate():
        print("form ok!",[form.name.data,form.email.data,form.id.data])
        recvd=request.files['files[]']

        if 'Content-Range' in request.headers and \
           "bytes 0-" not in request.headers['Content-Range']:
           mode="ab"
        else: 
           mode="wb"
       
        save_upload(recvd,mode,
           os.path.join("frobozz",secure_filename(recvd.filename)))

        return redirect(url_for('upload'))
    return render_template('upload.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user=[form.username.data, form.email.data,form.password.data]
        flash('Thanks for registering')
        return redirect(url_for('register'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
