import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).parents[1]
PYTHON_CANDIDATES = ("python3.14", "python3.13", "python3.12", "python3.11", "python3")


def _write_executable(path, contents):
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _write_python_candidates(bin_dir, supported_name=None):
    for name in PYTHON_CANDIDATES:
        supported = name == supported_name
        version = "3.14.0" if supported else "3.10.14"
        _write_executable(
            bin_dir / name,
            (
                "#!/bin/sh\n"
                f'if [ "$1" = "-c" ]; then exit {0 if supported else 1}; fi\n'
                f"printf 'Python {version}\\n'\n"
            ),
        )


def _run_setup(tmp_path, path, answer="n\n", args=()):
    shutil.copy(PROJECT_ROOT / "setup.sh", tmp_path / "setup.sh")
    shutil.copy(PROJECT_ROOT / ".env-sample", tmp_path / ".env-sample")

    return subprocess.run(
        ["bash", "setup.sh", *args],
        cwd=tmp_path,
        env={**os.environ, "PATH": path},
        input=answer,
        capture_output=True,
        text=True,
        check=False,
    )


def test_setup_rejects_unsupported_python(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_python_candidates(bin_dir)
    _write_executable(bin_dir / "uv", "#!/bin/sh\nexit 0\n")

    result = _run_setup(tmp_path, f"{bin_dir}:/usr/bin:/bin")

    assert result.returncode != 0
    assert "Python 3.11 or newer is required" in result.stdout


@pytest.mark.parametrize("python_name", ["python3", "python3.14"])
@pytest.mark.parametrize("mode", ["local", "full", "docker"])
def test_setup_installs_dependencies_for_selected_mode(tmp_path, python_name, mode):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_python_candidates(bin_dir, supported_name=python_name)
    _write_executable(
        bin_dir / "uv",
        "#!/bin/sh\nprintf '%s\\n' \"$@\" > uv-args.txt\n",
    )

    result = _run_setup(
        tmp_path,
        f"{bin_dir}:/usr/bin:/bin",
        answer="y\n" if mode == "docker" else "n\n",
        args=("--full",) if mode == "full" else (),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    uv_args = (tmp_path / "uv-args.txt").read_text().splitlines()
    expected = [
        "sync",
        "--python",
        str(bin_dir / python_name),
        "--extra",
        "dev",
    ]
    if mode != "local":
        expected += ["--extra", "full"]
    assert uv_args == expected


@pytest.mark.parametrize("full", [False, True])
def test_setup_configures_local_sessions_for_the_application(tmp_path, full):
    if full:
        pytest.importorskip("redis", reason="Full setup requires the Redis dependency")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_python_candidates(bin_dir, supported_name="python3")
    _write_executable(bin_dir / "uv", "#!/bin/sh\nexit 0\n")

    result = _run_setup(
        tmp_path,
        f"{bin_dir}:/usr/bin:/bin",
        args=("--full",) if full else (),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    config_result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from enferno.settings import Config; "
                "print(Config.SESSION_TYPE); "
                "print(Config.SESSION_COOKIE_SECURE); "
                "print(bool(Config.CELERY_BROKER_URL)); "
                "print(bool(Config.CELERY_RESULT_BACKEND))"
            ),
        ],
        cwd=tmp_path,
        env={
            "PATH": os.environ["PATH"],
            "PYTHONPATH": str(PROJECT_ROOT),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert config_result.returncode == 0, config_result.stderr
    assert config_result.stdout.splitlines() == (
        ["redis", "False", "True", "True"]
        if full
        else ["sqlalchemy", "False", "False", "False"]
    )


def test_setup_rejects_unknown_option_without_changing_environment(tmp_path):
    (tmp_path / ".env").write_text("KEEP=this\n")
    result = _run_setup(tmp_path, "/usr/bin:/bin", args=("--unknown",))
    assert result.returncode != 0
    assert "Unknown option: --unknown" in result.stdout
    assert (tmp_path / ".env").read_text() == "KEEP=this\n"


def test_setup_keeps_secure_cookies_for_docker(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_python_candidates(bin_dir, supported_name="python3")
    _write_executable(bin_dir / "uv", "#!/bin/sh\nexit 0\n")

    result = _run_setup(tmp_path, f"{bin_dir}:/usr/bin:/bin", answer="y\n")
    assert result.returncode == 0, result.stdout + result.stderr

    config = (tmp_path / ".env").read_text()
    assert "SESSION_COOKIE_SECURE=True" in config
    values = dotenv_values(tmp_path / ".env")
    assert values["SQLALCHEMY_DATABASE_URI"] == (
        f"postgresql://enferno:{values['DB_PASSWORD']}@postgres/enferno"
    )
    for setting, database in (
        ("REDIS_URL", 1),
        ("CELERY_BROKER_URL", 2),
        ("CELERY_RESULT_BACKEND", 3),
    ):
        assert values[setting] == (
            f"redis://:{values['REDIS_PASSWORD']}@redis:6379/{database}"
        )
