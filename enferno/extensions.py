# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""
from sqlalchemy.orm import DeclarativeBase

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
