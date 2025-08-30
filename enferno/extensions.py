"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_babel import Babel
from flask_caching import Cache
from flask_mail import Mail
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Optional dev dependency
try:
    from flask_debugtoolbar import DebugToolbarExtension

    debug_toolbar = DebugToolbarExtension()
except ImportError:
    debug_toolbar = None


class BaseModel(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=BaseModel)
cache = Cache()
mail = Mail()
session = Session()
babel = Babel()
