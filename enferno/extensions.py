"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_babel import Babel
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=BaseModel)
cache = Cache()
mail = Mail()
debug_toolbar = DebugToolbarExtension()
session = Session()
babel = Babel()
