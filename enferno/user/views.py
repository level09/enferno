import datetime

import orjson as json
from flask import Blueprint, request, flash, g, Response
from flask.templating import render_template
from flask_security import current_user, auth_required, roles_required

from enferno.extensions import db
from enferno.user.models import User, Role

bp_user = Blueprint('users', __name__, static_folder='../static')

PER_PAGE = 20


@bp_user.before_request
@auth_required('session')
@roles_required('admin')
def before_request():
    pass


@bp_user.route('/users/')
def users():
    roles = Role.query.all()
    roles = [r.to_dict() for r in roles]
    return render_template('cms/users.html', roles=roles)


@bp_user.route('/api/users')
def api_user():
    print([role for role in current_user.roles])
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', PER_PAGE, type=int)  # Set a default or use a config variable

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
        return {
            'message': 'Error creating user',
            'error': str(e)
            }, 412


@bp_user.post('/api/user/<int:id>')
def api_user_update(id):
    user = db.get_or_404(User, id)
    user_data = request.json.get('item', {})
    user.from_dict(user_data)
    db.session.commit()
    return {'message': 'User successfully updated!'}


@bp_user.route('/api/user/<int:id>', methods=['DELETE'])
def api_user_delete(id):
    user = db.get_or_404(User, id)
    db.session.delete(user)
    db.session.commit()
    return {'message': 'User successfully deleted!'}




@bp_user.route('/roles/')
def roles():
    return render_template('cms/roles.html')


@bp_user.route('/api/roles', methods=['GET'])
def api_roles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', PER_PAGE, type=int)

    query = db.session.query(Role)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = [role.to_dict() for role in pagination.items]

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


@bp_user.route('/api/role/', methods=['POST'])
def api_role_create():
    role_data = request.json.get('item', {})
    role = Role()
    role.from_dict(role_data)
    db.session.add(role)
    try:
        db.session.commit()
        return {'message': 'Role successfully created!'}
    except Exception as e:
        db.session.rollback()
        return {'message': 'Error creating role', 'error': str(e)}, 412


@bp_user.post('/api/role/<int:id>')
def api_role_update(id):
    role = db.get_or_404(Role, id)
    role_data = request.json.get('item', {})
    role.from_dict(role_data)
    db.session.commit()
    return {'message': 'Role successfully updated!'}


@bp_user.route('/api/role/<int:id>', methods=['DELETE'])
def api_role_delete(id):
    role = db.session.query(Role).get_or_404(id)
    db.session.delete(role)
    db.session.commit()
    return {'message': 'Role successfully deleted!'}
