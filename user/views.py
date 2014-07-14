from flask import Blueprint, request, session, redirect, url_for, flash, g
from flask.ext.security import login_required, logout_user, login_user, current_user
from flask.templating import render_template
from models import User
bp_user = Blueprint('user',__name__,'../static')


@bp_user.before_request
def before_request():
    g.user = User.objects.get(id=current_user)


@bp_user.route('/account/')
@login_required
def account():
    return render_template('account.html')
