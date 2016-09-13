import os

from app import create_app
from settings import DevConfig, ProdConfig

CONFIG = ProdConfig if os.environ.get('ENFERNO_ENV') == 'prod' else DevConfig

app = create_app(CONFIG)
