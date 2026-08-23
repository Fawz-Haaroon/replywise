#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${1:-$ROOT/replywise-bundle.zip}"
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$(pwd)/$OUTPUT"
fi
OUTPUT_DIR="$(dirname "$OUTPUT")"
OUTPUT_NAME="$(basename "$OUTPUT")"

if ! command -v zip >/dev/null 2>&1; then
  printf 'The zip utility is required to create the bundle.\n' >&2
  exit 1
fi
mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT"

cd "$ROOT"
zip -qr "$OUTPUT" . \
  -x '.venv/*' \
  -x '.env' \
  -x '.pytest_cache/*' \
  -x '*/.pytest_cache/*' \
  -x '__pycache__/*' \
  -x '*/__pycache__/*' \
  -x '*.pyc' \
  -x '.streamlit/*' \
  -x '.git/*' \
  -x '.mypy_cache/*' \
  -x '.ruff_cache/*' \
  -x '.coverage' \
  -x 'coverage.xml' \
  -x 'dist/*' \
  -x 'build/*' \
  -x '*.egg-info/*' \
  -x '*.log' \
  -x '*.tmp' \
  -x '*.swp' \
  -x '.DS_Store' \
  -x 'models/weights/*' \
  -x '*/models/weights/*' \
  -x "$OUTPUT_NAME" \
  -x '*.zip'

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    printf 'Python 3 is required to validate the generated bundle.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$OUTPUT" <<'PY'
from pathlib import Path
import sys
import zipfile

archive_path = Path(sys.argv[1])
required = {
    ".env.example",
    "README.md",
    "app.py",
    "config.py",
    "domain_types.py",
    "requirements.txt",
    "pyproject.toml",
    "scripts/create_bundle.sh",
    "scripts/install_arch_linux.sh",
    "scripts/run.sh",
    "scripts/pull_ollama_model.sh",
    "tests/test_cases.json",
    "domain/__init__.py",
    "domain/intake.py",
    "domain/context_analysis.py",
    "domain/drafting.py",
    "llm/__init__.py",
    "llm/client.py",
    "llm/prompts.py",
    "llm/providers/__init__.py",
    "llm/providers/offline_provider.py",
    "llm/providers/ollama_provider.py",
    "llm/providers/groq_provider.py",
    "llm/providers/gemini_provider.py",
    "llm/providers/http_support.py",
    "llm/providers/response_parsing.py",
    "responsible_ai/__init__.py",
    "responsible_ai/pii_scan.py",
    "responsible_ai/commitment_scan.py",
    "responsible_ai/assumption_scan.py",
    "responsible_ai/risk_score.py",
    "responsible_ai/disclosure.py",
    "ui/__init__.py",
    "ui/components.py",
    "tests/test_app_smoke.py",
    "tests/test_fixture_behavior.py",
    "tests/test_offline_grounding.py",
    "tests/test_ollama_integration.py",
    "tests/test_prompt_boundaries.py",
    "tests/test_assumption_scan.py",
    "tests/test_bundle_script.py",
    "tests/test_commitment_scan.py",
    "tests/test_configuration.py",
    "tests/test_drafting.py",
    "tests/test_pii_scan.py",
    "tests/test_provider_boundaries.py",
    "tests/test_risk_score.py",
}
forbidden_suffixes = (".pyc", ".zip", ".log", ".tmp", ".swp")
forbidden_parts = {
    ".env",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".streamlit",
    ".git",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
}

with zipfile.ZipFile(archive_path) as archive:
    names = set(archive.namelist())
    missing = sorted(required - names)
    forbidden = sorted(
        name for name in names
        if name.endswith(forbidden_suffixes)
        or any(part in forbidden_parts for part in Path(name).parts)
        or name.startswith("models/weights/")
    )
    if missing or forbidden:
        raise SystemExit(
            f"Bundle validation failed: missing={missing!r}, forbidden={forbidden!r}"
        )
    bad_python_layout = sorted(
        name for name in names
        if name.endswith(".py") and name.startswith("replywise/")
    )
    if bad_python_layout:
        raise SystemExit(
            "Bundle validation failed: flat canonical layout expected, "
            f"but found nested package files {bad_python_layout[:5]!r}"
        )
    bad_import_text = []
    for name in names:
        if name.endswith(".py"):
            text = archive.read(name).decode("utf-8")
            if (
                "from replywise" in text
                or "import replywise" in text
                or "replywise/app.py" in text
                or "replywise/tests" in text
            ):
                bad_import_text.append(name)
    if bad_import_text:
        raise SystemExit(
            "Bundle validation failed: stale package/path references found in "
            f"{bad_import_text!r}"
        )
    non_executable_scripts = sorted(
        name
        for name in names
        if name.startswith("scripts/") and name.endswith(".sh")
        and not (archive.getinfo(name).external_attr >> 16) & 0o111
    )
    if non_executable_scripts:
        raise SystemExit(
            "Bundle validation failed: shell scripts are not executable: "
            f"{non_executable_scripts!r}"
        )
    try:
        import json

        cases = json.loads(archive.read("tests/test_cases.json"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SystemExit(f"Bundle validation failed: invalid test fixture: {error}") from error
    if not isinstance(cases, list) or len(cases) != 60:
        raise SystemExit(
            "Bundle validation failed: tests/test_cases.json must contain 60 cases."
        )
    archive.testzip()

print(f"Validated bundle: {archive_path}")
PY

printf 'Created and validated %s\n' "$OUTPUT"