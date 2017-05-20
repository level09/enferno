from flask import Blueprint, request, session, redirect, url_for, flash, g
from flask_security import login_required, logout_user, login_user, current_user
from flask.templating import render_template
from enferno.user.models import User
bp_user = Blueprint('users',__name__,static_folder='../static')


@bp_user.before_request
def before_request():
    g.user = current_user

@bp_user.route('/account/')
@login_required
def account():
    return render_template('account.html')
