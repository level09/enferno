from flask import Blueprint, request, session, redirect, url_for, flash, g
from flask_security import login_required, logout_user, login_user, current_user
from flask_security.utils import hash_password, verify_password
from flask.templating import render_template
from enferno.user.models import User
bp_user = Blueprint('users',__name__,static_folder='../static')


@bp_user.before_request
def before_request():
    g.user = current_user

@bp_user.route('/dashboard/')
@login_required
def account():
    return render_template('dashboard.html')


@bp_user.route('/settings/', methods=['GET','POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form.get("name")
        if  name != '':
            user = User.query.get(session.get('user_id'))
            user.name = name
            flash('Save successful. ')
            user.save()
    return render_template('settings.html')


@bp_user.route('/change-password/', methods=['GET','POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user = User.query.get(session.get('user_id'))
        oldpass = request.form.get("oldpass")
        if not verify_password(oldpass, user.password):
            flash('Wrong password entered.')
        else:
            password = request.form.get('password')
            if password != '':
                user.password = hash_password(password)
                user.save()
                flash ('Password changed successfully. ')
    return render_template('change-password.html')