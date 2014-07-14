from flask import Flask, request, abort, Response, redirect, url_for, flash, Blueprint
from flask.templating import render_template


bp_public = Blueprint('public',__name__, static_folder='../static')



@bp_public.route('/')
def index():
    return render_template('index.html')


@bp_public.route('/docs')
def docs():
    return render_template('docs.html')
