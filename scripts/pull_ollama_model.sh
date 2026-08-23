#!/usr/bin/env bash
set -euo pipefail

MODEL="${1:-llama3.2:3b}"
if [[ -z "$MODEL" || "$MODEL" == -* ]]; then
  printf 'Usage: %s [model-name]\n' "$0" >&2
  exit 2
fi
if ! command -v ollama >/dev/null 2>&1; then
  printf 'Ollama was not found on PATH. Install Ollama before pulling a model.\n' >&2
  exit 1
fi
BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
BASE_URL="${BASE_URL%/}"
if ! command -v curl >/dev/null 2>&1; then
  printf 'curl is required to verify the existing Ollama service.\n' >&2
  exit 1
fi
if ! curl --fail --silent --show-error --max-time 5 "$BASE_URL/api/tags" >/dev/null; then
  printf 'Ollama is installed but its local service is not responding at %s.\n' "$BASE_URL" >&2
  printf 'Start the existing service with your system service manager; this script will not start a second server.\n' >&2
  exit 1
fi
ollama pull "$MODEL"
printf '\nPulled local model: %s\n' "$MODEL"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf 'Set OLLAMA_MODEL=%s and LLM_PROVIDER=ollama in %s/.env\n' "$MODEL" "$ROOT"