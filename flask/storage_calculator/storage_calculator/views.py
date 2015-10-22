import json
import time
from storage_calculator import app
from flask import render_template, flash, redirect, url_for, session, g, request, jsonify, abort
from flask.ext.security import login_required
from flask.ext.login import login_user, logout_user
from authentication import LoginForm, User
from storage_calculator.storage import CostCalculator

   
@app.route("/")
@login_required
def index():
    """
    index renders the storage cost calculator.
    """
    return render_template('index.html')

@app.route("/usage")
@login_required
def storath():
    """
    render the base usage page
    """
    return render_template('usage.html')

@app.route("/api/calculate/json", methods=['POST'])
@login_required
def api_calculate():
    time.sleep(1)
    print request.headers['Content-Type']
    if 'application/json' in request.headers['Content-Type']:
        fields = request.json
        cc = CostCalculator(hss_units=float(fields['secure_gb']),
            ffs_units=float(fields['fast_file_tb']),
            es_units=float(fields['economy_tb']),
            unit_growth=(float(fields['growth_rate']) / 100),
            rate_decline=(float(fields['cost_decline']) / 100)
        )
        cc.calculate(year_count=5)
        # probably want to use jsonify to return proper content-type...
        #return cc.cost_json()
        return jsonify(cc.years)
    else:
        abort(500)


def login():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(u'Successfully logged in as %s' % form.user.name)
        session['user_id'] = request.form['username']
        login_user(form.user)
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    g.username = ''
    return render_template('logout.html')

if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })

