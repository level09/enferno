"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from quart_session import Session
from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=BaseModel)
session = Session()
babel = Babel()

# OAuth configuration is stored in app.config and used directly in routes
