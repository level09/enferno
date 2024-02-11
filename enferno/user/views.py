import datetime

import orjson as json
from flask import Blueprint, request, flash, g, Response
from flask.templating import render_template
from flask_security import login_required, current_user

from enferno.extensions import db
from enferno.user.models import User, Role

bp_user = Blueprint('users', __name__, static_folder='../static')


@bp_user.before_request
def before_request():
    g.user = current_user


@bp_user.route('/dashboard/')
@login_required
def account():
    return render_template('dashboard.html')


@bp_user.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    name = request.form.get("name")
    if name != '':
        user = User.query.get(current_user.id)
        user.name = name
        flash('Save successful. ')
        user.save()
    return render_template('settings.html')


# adding user management
PER_PAGE = 30


@bp_user.route('/users/')
@login_required
def user():
    roles = Role.query.all()
    roles = [r.to_dict() for r in roles]
    return render_template('cms/users.html', roles=roles)


@bp_user.route('/api/users')
@login_required
def api_user():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Set a default or use a config variable

    # Use Flask-SQLAlchemy's paginate method on the query
    query = db.session.query(User)
    pagination = db.paginate(query, page=page, per_page=per_page, count=True)

    items = [user.to_dict() for user in pagination.items]  # Assuming a to_dict method on your User model

    # Construct the response dictionary
    response_data = {
        'items': items,
        'perPage': pagination.per_page,
        'page': pagination.page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num
    }

    return Response(json.dumps(response_data), content_type='application/json')


@bp_user.post('/api/user/')
@login_required
def api_user_create():
    user_data = request.json.get('item', {})
    user = User()
    user.from_dict(user_data)  # Assuming from_dict is correctly implemented
    user.confirmed_at = datetime.datetime.now()
    db.session.add(user)
    try:
        db.session.commit()
        return {'message': 'User successfully created!'}
    except Exception as e:
        db.session.rollback()
        return Response(json.dumps({'message': 'Save Failed', 'error': str(e)}), status=417,
                        content_type='application/json')


@bp_user.post('/api/user/<int:id>')
@login_required
def api_user_update(id):
    user = User.query.get_or_404(id)
    user_data = request.json.get('item', {})
    user.from_dict(user_data)
    db.session.commit()
    return {'message': 'User successfully updated!'}


@bp_user.route('/api/user/<int:id>', methods=['DELETE'])
@login_required
def api_user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return {'message': 'User successfully deleted!'}
