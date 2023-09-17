from flask import request, Blueprint, send_from_directory
from flask.templating import render_template

public = Blueprint('public',__name__, static_folder='../static')
@public.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=10800'
    return response

@public.route('/')
def index():
    return render_template('index.html')


@public.route('/robots.txt')
def static_from_root():
    return send_from_directory(public.static_folder, request.path[1:])