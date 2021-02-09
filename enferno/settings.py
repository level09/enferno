# -*- coding: utf-8 -*-
import os
import redis

os_env = os.environ


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', '3nF3Rn0')
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    # SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/enferno.db'
    # for postgres
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql:///enferno')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/10')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/11')

    # security
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT','3nF3Rn0')

    SECURITY_POST_LOGIN_VIEW = '/dashboard'
    SECURITY_POST_CONFIRM_VIEW = '/dashboard'

    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS', 'redis://localhost:6379/1'))
    PERMANENT_SESSION_LIFETIME = 3600

    # flask mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SECURITY_EMAIL_SENDER = os.environ.get('SECURITY_EMAIL_SENDER', 'info@domain.com')


class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    # SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@localhost/enferno'
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_ENABLED = True
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
