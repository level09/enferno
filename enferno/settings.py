import os
from datetime import timedelta

import bleach
import redis
from dotenv import load_dotenv

os_env = os.environ
load_dotenv()


def uia_username_mapper(identity):
    # Sanitize and strip whitespace from email input - Flask-Security handles case insensitivity
    return bleach.clean(identity, strip=True).strip() if identity else identity


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "3nF3Rn0")
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    DEBUG_TB_ENABLED = os.environ.get("DEBUG_TB_ENABLED")
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "simple"  # Can be "memcached", "redis", etc.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "postgresql:///enferno"
    )
    # for postgres
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql:///enferno')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/3"
    )

    # security
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = False
    SECURITY_CONFIRMABLE = False
    SECURITY_CHANGEABLE = True  # Password changes allowed
    SECURITY_TRACKABLE = True

    # Disable email changes - critical for multi-tenant SaaS
    SECURITY_EMAIL_CHANGEABLE = False
    SECURITY_PASSWORD_HASH = "argon2"
    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT",
        "e89c4039b51f72b0519d1ee033ff537c7c48902e1f497f74c7a0923c9e4e0996",
    )
    # Email-only login - simplest and most user-friendly
    SECURITY_USER_IDENTITY_ATTRIBUTES = [
        {"email": {"mapper": uia_username_mapper, "case_insensitive": True}},
    ]
    SECURITY_USERNAME_ENABLE = False  # Disable username completely

    SECURITY_POST_LOGIN_VIEW = "/dashboard"
    SECURITY_POST_CONFIRM_VIEW = "/dashboard"
    SECURITY_POST_REGISTER_VIEW = "/login"

    SECURITY_MULTI_FACTOR_RECOVERY_CODES = True
    SECURITY_MULTI_FACTOR_RECOVERY_CODES_N = 3
    SECURITY_MULTI_FACTOR_RECOVERY_CODES_KEYS = None
    SECURITY_MULTI_FACTOR_RECOVERY_CODE_TTL = None

    SECURITY_TWO_FACTOR_ENABLED_METHODS = ["authenticator"]
    SECURITY_TWO_FACTOR = True
    SECURITY_API_ENABLED_METHODS = ["session"]

    SECURITY_FRESHNESS = timedelta(minutes=60)
    SECURITY_FRESHNESS_GRACE_PERIOD = timedelta(minutes=60)
    SECURITY_PASSWORD_LENGTH_MIN = 12

    SECURITY_TOTP_SECRETS = {"1": os.environ.get("SECURITY_TOTP_SECRETS")}
    SECURITY_TOTP_ISSUER = "Enferno"

    SECURITY_WEBAUTHN = True
    SECURITY_WAN_ALLOW_AS_FIRST_FACTOR = True
    SECURITY_WAN_ALLOW_AS_MULTI_FACTOR = True
    SECURITY_WAN_ALLOW_AS_VERIFY = ["first", "secondary"]
    SECURITY_WAN_ALLOW_USER_HINTS = True

    SESSION_PROTECTION = "strong"

    # Session configuration
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(
        os.environ.get("REDIS_SESSION", "redis://localhost:6379/1")
    )
    SESSION_KEY_PREFIX = "session:"
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = (
        os.environ.get("SESSION_COOKIE_HTTPONLY", "True").lower() == "true"
    )
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")

    # flask mail settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    SECURITY_EMAIL_SENDER = os.environ.get("SECURITY_EMAIL_SENDER", "info@domain.com")
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False

    # Google OAuth Settings
    GOOGLE_AUTH_ENABLED = (
        os.environ.get("GOOGLE_AUTH_ENABLED", "False").lower() == "true"
    )
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
        "GOOGLE_OAUTH_REDIRECT_URI"
    )  # Let the OAuth handler construct it dynamically
    OAUTHLIB_INSECURE_TRANSPORT = os.environ.get(
        "OAUTHLIB_INSECURE_TRANSPORT", "1"
    )  # Remove in production

    # GitHub OAuth Settings
    GITHUB_AUTH_ENABLED = (
        os.environ.get("GITHUB_AUTH_ENABLED", "False").lower() == "true"
    )
    GITHUB_OAUTH_CLIENT_ID = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
    GITHUB_OAUTH_CLIENT_SECRET = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
