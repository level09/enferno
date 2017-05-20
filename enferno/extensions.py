# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_mongoengine import MongoEngine
db = MongoEngine()


from flask_cache import Cache
cache = Cache()

from flask_mail import Mail
mail = Mail()

from flask_debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()
