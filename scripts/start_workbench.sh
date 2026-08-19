#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${QAP_RUN_ROOT:-$ROOT/runs}"
CAPTURE_ROOT="${QAP_API_CAPTURE_ROOT:-$RUN_ROOT/public-capture}"

mkdir -p "$RUN_ROOT" "$CAPTURE_ROOT"

api_is_qap() {
  curl -fsS --max-time 1 http://127.0.0.1:8000/api/health 2>/dev/null \
    | grep -q '"schema_version":"qap.api.health.v1"'
}

web_is_qap() {
  curl -fsS --max-time 1 http://127.0.0.1:5173/ 2>/dev/null \
    | grep -q '<title>QAP Research Workbench</title>'
}

port_is_busy() {
  ss -ltnH "sport = :$1" | grep -q .
}

if api_is_qap && web_is_qap; then
  printf 'QAP workbench is already running.\n'
  printf '  Web: http://localhost:5173\n'
  printf '  API: http://127.0.0.1:8000\n'
  exit 0
fi

if port_is_busy 8000; then
  printf 'Cannot start QAP: port 8000 is already in use.\n' >&2
  exit 1
fi
if port_is_busy 5173; then
  printf 'Cannot start QAP: port 5173 is already in use.\n' >&2
  exit 1
fi

api_pid=""
web_pid=""
cleanup() {
  trap - EXIT INT TERM
  set +e
  if [[ -n "$web_pid" ]]; then
    kill -TERM -- "-$web_pid" 2>/dev/null
    wait "$web_pid" 2>/dev/null
  fi
  if [[ -n "$api_pid" ]]; then
    kill -TERM -- "-$api_pid" 2>/dev/null
    wait "$api_pid" 2>/dev/null
  fi
}
trap cleanup EXIT INT TERM

QAP_API_RUN_ROOT="$RUN_ROOT" \
QAP_API_MARKET_DATA_ROOT="${QAP_API_MARKET_DATA_ROOT:-$ROOT}" \
QAP_API_REPOSITORY_ROOT="${QAP_API_REPOSITORY_ROOT:-$ROOT}" \
QAP_API_CAPTURE_ROOT="$CAPTURE_ROOT" \
setsid bash -c '
  cd "$1"
  exec uv run uvicorn qap.api.app:create_default_app \
    --factory --host 127.0.0.1 --port 8000 --workers 1
' _ "$ROOT" &
api_pid=$!

setsid bash -c '
  cd "$1/web"
  exec pnpm dev --host 127.0.0.1 --port 5173
' _ "$ROOT" &
web_pid=$!

printf 'QAP workbench starting...\n'
printf '  Web: http://localhost:5173\n'
printf '  API: http://127.0.0.1:8000\n'
printf '  Runs: %s\n' "$RUN_ROOT"
printf 'Press Ctrl+C to stop both processes.\n\n'

wait -n "$api_pid" "$web_pid"
