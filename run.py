import os
from enferno.app import create_app
from enferno.settings import DevConfig, ProdConfig

CONFIG = ProdConfig if os.environ.get('FLASK_DEBUG') == '0' else DevConfig

app = create_app(CONFIG)
