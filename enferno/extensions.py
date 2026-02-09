"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from quart_session import Session
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = None
async_session_factory = None
session = Session()
