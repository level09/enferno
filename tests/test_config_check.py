import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture
def config_command(tmp_path):
    shutil.copy(ROOT / "checks.py", tmp_path / "checks.py")
    shutil.copy(ROOT / ".env-sample", tmp_path / ".env-sample")
    package = tmp_path / "enferno"
    package.mkdir()
    for name in ("__init__.py", "settings.py"):
        shutil.copy(ROOT / "enferno" / name, package / name)

    def run(settings=None, args=(), missing_packages=()):
        values = {
            "SECRET_KEY": "private-test-secret",
            "SECURITY_PASSWORD_SALT": "private-test-salt",
            "SECURITY_TOTP_SECRETS": "private-test-totp",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///must-not-be-created.sqlite3",
        }
        values.update(settings or {})
        (tmp_path / ".env").write_text(
            "\n".join(f"{key}={value}" for key, value in values.items())
        )
        # Simulate a lean installation without changing the developer's environment.
        script = (
            "import builtins, importlib.util, runpy\n"
            "original = importlib.util.find_spec\n"
            "original_import = builtins.__import__\n"
            f"missing = {missing_packages!r}\n"
            "importlib.util.find_spec = lambda name: None if name in missing else original(name)\n"
            "def checked_import(name, *args, **kwargs):\n"
            '    if name.split(".")[0] in missing: raise ModuleNotFoundError(name)\n'
            "    return original_import(name, *args, **kwargs)\n"
            "builtins.__import__ = checked_import\n"
            "runpy.run_path('checks.py', run_name='__main__')"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, "--config", *args],
            cwd=tmp_path,
            env={"PATH": os.environ["PATH"]},
            capture_output=True,
            text=True,
            check=False,
        )
        assert not list(tmp_path.rglob("*.sqlite3"))
        assert "Traceback" not in result.stderr
        for secret in ("private-test-secret", "private-test-salt", "private-test-totp"):
            assert secret not in result.stdout + result.stderr
        return result

    return run


def test_lean_config_needs_no_services_or_app_startup(config_command):
    result = config_command(missing_packages=("redis", "celery"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Configuration checks passed" in result.stdout


@pytest.mark.parametrize(
    "key", ["SECRET_KEY", "SECURITY_PASSWORD_SALT", "SECURITY_TOTP_SECRETS"]
)
def test_missing_secret_names_the_setting_without_traceback(config_command, key):
    result = config_command({key: ""})
    assert result.returncode == 1
    assert key in result.stdout
    assert "setup.sh" in result.stdout


def test_config_reports_enabled_oauth_with_placeholder_credentials(config_command):
    result = config_command(
        {
            "GOOGLE_AUTH_ENABLED": "True",
            "GOOGLE_OAUTH_CLIENT_ID": "your_google_client_id",
        }
    )
    assert result.returncode == 1
    assert "GOOGLE_OAUTH_CLIENT_ID" in result.stdout
    assert "GOOGLE_OAUTH_CLIENT_SECRET" in result.stdout


@pytest.mark.parametrize(
    "setting,packages",
    [("REDIS_SESSION", ("redis",)), ("CELERY_BROKER_URL", ("celery",))],
)
def test_config_reports_missing_optional_dependency(config_command, setting, packages):
    result = config_command(
        {setting: "redis://localhost:6379/1"}, missing_packages=packages
    )
    assert result.returncode == 1
    assert "uv sync --extra dev --extra full" in result.stdout


def test_invalid_database_url_does_not_print_credentials(config_command):
    value = "broken-url-with-private-password"
    result = config_command({"SQLALCHEMY_DATABASE_URI": value})
    assert result.returncode == 1
    assert "SQLALCHEMY_DATABASE_URI" in result.stdout
    assert value not in result.stdout + result.stderr


def test_invalid_sqlite_url_structure_fails(config_command):
    result = config_command({"SQLALCHEMY_DATABASE_URI": "sqlite://local.sqlite3"})
    assert result.returncode == 1
    assert "SQLALCHEMY_DATABASE_URI" in result.stdout


def test_missing_database_driver_fails_without_connecting(config_command):
    result = config_command(
        {"SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://localhost/example"},
        missing_packages=("psycopg",),
    )
    assert result.returncode == 1
    assert "SQLALCHEMY_DATABASE_URI" in result.stdout
    assert "driver" in result.stdout


def test_invalid_redis_url_does_not_print_credentials(config_command):
    pytest.importorskip("redis")
    value = "https://private-password@example.com"
    result = config_command({"REDIS_SESSION": value})
    assert result.returncode == 1
    assert "REDIS" in result.stdout
    assert value not in result.stdout + result.stderr


def test_redis_url_precedence_matches_application(config_command):
    pytest.importorskip("redis")
    result = config_command(
        {
            "REDIS_URL": "redis://localhost:6379/1",
            "REDIS_SESSION": "invalid-ignored-url",
        }
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sample_core_secrets_fail(config_command):
    result = config_command({"SECRET_KEY": "3nF3Rn@"})
    assert result.returncode == 1
    assert "placeholder" in result.stdout
    assert "3nF3Rn@" not in result.stdout


def test_celery_result_backend_requires_a_broker(config_command):
    result = config_command({"CELERY_RESULT_BACKEND": "redis://localhost:6379/3"})
    assert result.returncode == 1
    assert "CELERY_BROKER_URL: required" in result.stdout
