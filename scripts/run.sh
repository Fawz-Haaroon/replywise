#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  printf 'Python 3 is required. Run scripts/install_arch_linux.sh first.\n' >&2
  exit 1
fi
if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)'; then
  printf 'ReplyWise requires Python 3.11.x; found ' >&2
  "$PYTHON_BIN" --version >&2
  printf 'Recreate the project virtual environment with scripts/install_arch_linux.sh.\n' >&2
  exit 1
fi
if ! "$PYTHON_BIN" -c 'import streamlit' >/dev/null 2>&1; then
  printf 'Streamlit is not installed for %s. Run scripts/install_arch_linux.sh first.\n' "$PYTHON_BIN" >&2
  exit 1
fi
exec "$PYTHON_BIN" -m streamlit run "$ROOT/app.py" \
  --server.headless true \
  --browser.gatherUsageStats false \
  --server.port "${PORT:-8501}" \
  --server.address "${HOST:-127.0.0.1}"