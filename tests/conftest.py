import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "test-password-salt")
os.environ.setdefault("SECURITY_TOTP_SECRETS", "test-totp-secret")

from flask_security.utils import hash_password  # noqa: E402

from enferno.app import create_app  # noqa: E402
from enferno.extensions import db  # noqa: E402
from enferno.settings import Config  # noqa: E402
from enferno.user.models import Role, User  # noqa: E402

PASSWORD = "correct horse battery staple"


class TestConfig(Config):
    TESTING = True
    # Tests drop every table: point TEST_DATABASE_URI at a disposable database.
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI", "sqlite://")
    SESSION_TYPE = "sqlalchemy"
    SESSION_REDIS = None
    WTF_CSRF_ENABLED = False
    CELERY_BROKER_URL = None
    CELERY_RESULT_BACKEND = None


@pytest.fixture(scope="session")
def app():
    return create_app(TestConfig)


# Tests must not hold an app context open: requests would reuse it and leak
# login state between them. Open one explicitly for direct database access.
@pytest.fixture(autouse=True)
def database(app):
    with app.app_context():
        db.create_all()
    yield
    with app.app_context():
        db.drop_all()


@pytest.fixture
def make_user(app):
    def make(email, *roles):
        with app.app_context():
            user = User(email=email, password=hash_password(PASSWORD), active=True)
            for name in roles:
                user.roles.append(Role(name=name))
            db.session.add(user)
            db.session.commit()
        return email

    return make


@pytest.fixture
def login(app):
    def log_in(email):
        client = app.test_client()
        response = client.post("/login", data={"email": email, "password": PASSWORD})
        assert response.status_code == 302, response.status_code
        return client

    return log_in


@pytest.fixture
def admin_client(make_user, login):
    return login(make_user("admin@example.com", "admin"))
