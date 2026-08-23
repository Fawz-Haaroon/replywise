#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ReplyWise requires Python 3.11.x.
# Prefer the explicit Python 3.11 executable instead of relying on
# the system's generic `python3`, which may point to a newer release.
if command -v python3.11 >/dev/null 2>&1; then
  SYSTEM_PYTHON="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
  SYSTEM_PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  SYSTEM_PYTHON="$(command -v python)"
else
  printf 'Python 3.11 is required but was not found on PATH.\n' >&2
  printf 'Install Python 3.11 and rerun this installer.\n' >&2
  exit 1
fi

printf 'Using '
"$SYSTEM_PYTHON" --version

if ! "$SYSTEM_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)'; then
  printf 'ReplyWise requires Python 3.11.x; found ' >&2
  "$SYSTEM_PYTHON" --version >&2
  printf 'Please install Python 3.11 and make sure python3.11 is available on PATH.\n' >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  "$SYSTEM_PYTHON" -m venv .venv
fi

if ! .venv/bin/python -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)'; then
  printf 'Existing %s/.venv uses an incompatible Python. Remove it and rerun this installer.\n' "$ROOT" >&2
  .venv/bin/python --version >&2 || true
  exit 1
fi

source .venv/bin/activate

python -m pip --version >/dev/null
python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  printf 'Created %s/.env from .env.example.\n' "$ROOT"
else
  printf 'Preserved existing %s/.env.\n' "$ROOT"
fi

printf '\nReplyWise is installed.\n'
printf 'Edit %s/.env if needed, then run:\n' "$ROOT"
printf 'source %s/.venv/bin/activate && %s/scripts/run.sh\n' "$ROOT" "$ROOT"
