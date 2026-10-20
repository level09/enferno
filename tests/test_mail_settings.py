import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture
def mail_settings(tmp_path):
    # Load settings away from the developer's .env, which load_dotenv() would read.
    package = tmp_path / "enferno"
    package.mkdir()
    for name in ("__init__.py", "settings.py"):
        shutil.copy(ROOT / "enferno" / name, package / name)
    (tmp_path / ".env").write_text(
        "SECRET_KEY=test-secret\n"
        "SECURITY_PASSWORD_SALT=test-salt\n"
        "SECURITY_TOTP_SECRETS=test-totp\n"
        "SQLALCHEMY_DATABASE_URI=sqlite:///must-not-be-created.sqlite3\n"
    )

    def run(env=None):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from enferno.settings import Config; "
                "print(Config.MAIL_PORT, Config.MAIL_USE_SSL, Config.MAIL_USE_TLS)",
            ],
            cwd=tmp_path,
            env={"PATH": os.environ["PATH"], **(env or {})},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    return run


def test_mail_defaults_to_ssl_on_465(mail_settings):
    assert mail_settings() == "465 True False"


def test_mail_port_ssl_and_tls_come_from_env(mail_settings):
    env = {"MAIL_PORT": "587", "MAIL_USE_SSL": "False", "MAIL_USE_TLS": "True"}
    assert mail_settings(env) == "587 False True"
