import shutil
import stat
import subprocess
from pathlib import Path

import pytest
from dotenv import dotenv_values

ROOT = Path(__file__).parents[1]
PYTHONS = ("python3.14", "python3.13", "python3.12", "python3.11", "python3")


def _executable(path, body):
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def setup(tmp_path):
    """Run a copy of setup.sh with fake python and uv, stdin not a terminal."""
    shutil.copy(ROOT / "setup.sh", tmp_path)
    shutil.copy(ROOT / ".env-sample", tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _executable(bin_dir / "uv", "printf '%s\\n' \"$@\" > uv-args.txt")

    def run(*args, python="python3"):
        for name in PYTHONS:
            ok = name == python
            _executable(
                bin_dir / name,
                f'[ "$1" = "-c" ] && exit {0 if ok else 1}; echo "Python 3.{14 if ok else 10}"',
            )
        return subprocess.run(
            ["bash", "setup.sh", *args],
            cwd=tmp_path,
            env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    return run


def test_rejects_unsupported_python(setup):
    result = setup(python=None)
    assert result.returncode == 1
    assert "Python 3.11 or newer is required" in result.stdout


@pytest.mark.parametrize(
    "args,extras",
    [((), ["dev"]), (("--full",), ["dev", "full"]), (("--docker",), ["dev", "full"])],
)
def test_installs_extras_for_mode(setup, tmp_path, args, extras):
    result = setup(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    uv_args = (tmp_path / "uv-args.txt").read_text().split()
    assert uv_args[uv_args.index("--extra") :] == [
        a for e in extras for a in ("--extra", e)
    ]


def test_generates_secrets_and_local_defaults(setup, tmp_path):
    assert setup().returncode == 0
    env = dotenv_values(tmp_path / ".env")
    sample = dotenv_values(tmp_path / ".env-sample")
    for key in ("SECRET_KEY", "SECURITY_PASSWORD_SALT"):
        assert len(env[key]) == 32 and env[key] != sample.get(key)
    assert "SQLALCHEMY_DATABASE_URI" not in env
    assert not env.get("REDIS_URL")


def test_docker_wires_services_to_generated_passwords(setup, tmp_path):
    assert setup("--docker").returncode == 0
    env = dotenv_values(tmp_path / ".env")
    assert env["SQLALCHEMY_DATABASE_URI"] == (
        f"postgresql://enferno:{env['DB_PASSWORD']}@postgres/enferno"
    )
    assert env["REDIS_URL"] == f"redis://:{env['REDIS_PASSWORD']}@redis:6379/1"


def test_never_overwrites_env_without_a_terminal(setup, tmp_path):
    (tmp_path / ".env").write_text("KEEP=this\n")
    result = setup()
    assert result.returncode == 1
    assert "already exists" in result.stdout
    assert (tmp_path / ".env").read_text() == "KEEP=this\n"
    assert not (tmp_path / "uv-args.txt").exists()


def test_unknown_option_changes_nothing(setup, tmp_path):
    result = setup("--bogus")
    assert result.returncode == 1
    assert not (tmp_path / ".env").exists()
