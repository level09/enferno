# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""
from sqlalchemy.orm import DeclarativeBase
import os

class BaseModel(DeclarativeBase):
    pass

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(model_class=BaseModel)

from flask_caching import Cache
cache = Cache()

from flask_mail import Mail
mail = Mail()

from flask_debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()


from flask_session import Session
session = Session()

from flask_babel import Babel
babel = Babel()

from flask_openai import OpenAI
openai = OpenAI()

from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint

# Create blueprint without storage - we'll configure it in app.py
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    reprompt_select_account=False
)

github_bp = make_github_blueprint(
    client_id=os.environ.get("GITHUB_OAUTH_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_OAUTH_CLIENT_SECRET"),
    scope=["user:email"]  # Minimum scope needed for email
)