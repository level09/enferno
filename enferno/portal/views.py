from flask import Blueprint
from flask.templating import render_template
from flask_security import auth_required

portal = Blueprint('portal', __name__, static_folder='../static')

@portal.before_request
@auth_required('session')
def before_request():
    pass
@portal.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=10800'
    return response


@portal.route('/dashboard/')
def dashboard():
    return render_template('dashboard.html')

