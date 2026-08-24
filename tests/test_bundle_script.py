import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCRIPT = PROJECT_ROOT / "scripts" / "create_bundle.sh"


def test_bundle_script_creates_extractable_self_consistent_project(tmp_path):
    if os.environ.get("REPLYWISE_BUNDLE_CHILD_TEST") == "1":
        pytest.skip("The extracted-suite check must not recursively create another bundle.")

    output = tmp_path / "replywise-bundle.zip"
    result = subprocess.run(
        [str(BUNDLE_SCRIPT), str(output)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output.exists()

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "app.py" in names
        assert "scripts/run.sh" in names
        assert "tests/test_cases.json" in names
        assert ".env.example" in names
        assert not any(
            part in {"__pycache__", ".pytest_cache", ".venv", ".env"}
            or name.endswith((".pyc", ".zip"))
            for name in names
            for part in Path(name).parts
        )
        cases = json.loads(archive.read("tests/test_cases.json"))
        assert len(cases) == 60

        archive.extractall(tmp_path / "extracted")

    extracted = tmp_path / "extracted"
    # zipfile.extractall() intentionally does not restore Unix executable bits.
    # A normal `unzip` on Linux does; restore them here before testing the
    # extracted bundle's own generator.
    for script in (extracted / "scripts").glob("*.sh"):
        script.chmod(0o755)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(extracted)
    env["REPLYWISE_BUNDLE_CHILD_TEST"] = "1"
    test_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=extracted,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert test_run.returncode == 0, test_run.stdout + test_run.stderr


def test_bundle_script_resolves_relative_output_from_callers_working_directory(tmp_path):
    result = subprocess.run(
        ["bash", str(BUNDLE_SCRIPT), "relative-bundle.zip"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "relative-bundle.zip").is_file()
    assert "Created and validated" in result.stdout