#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${QAP_RUN_ROOT:-$ROOT/runs}"
WORKSPACE_MODE="${QAP_API_WORKSPACE_MODE:-local_market}"

case "$WORKSPACE_MODE" in
  sample|local_market) ;;
  *)
    printf 'Cannot start QAP: QAP_API_WORKSPACE_MODE must be sample or local_market.\n' >&2
    exit 1
    ;;
esac

mkdir -p "$RUN_ROOT"
RUN_ROOT="$(cd "$RUN_ROOT" && pwd -P)"
CAPTURE_ROOT="${QAP_API_CAPTURE_ROOT:-$RUN_ROOT/public-capture}"
mkdir -p "$CAPTURE_ROOT"
CAPTURE_ROOT="$(cd "$CAPTURE_ROOT" && pwd -P)"

api_is_qap() {
  curl -fsS --max-time 1 http://127.0.0.1:8000/api/health 2>/dev/null \
    | grep -q '"schema_version":"qap.api.health.v1"'
}

api_workspace_status() {
  curl -fsS --max-time 1 http://127.0.0.1:8000/api/workspace 2>/dev/null
}

workspace_status_is_valid() {
  printf '%s' "$1" | python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError):
    raise SystemExit(1)

valid = (
    payload.get("schema_version") == "qap.api.workspace_status.v1"
    and payload.get("workspace_mode") in {"sample", "local_market"}
    and isinstance(payload.get("workspace_root"), str)
)
raise SystemExit(0 if valid else 1)
'
}

workspace_matches_intent() {
  printf '%s' "$1" | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
matches = (
    payload["workspace_mode"] == sys.argv[1]
    and payload["workspace_root"] == sys.argv[2]
)
raise SystemExit(0 if matches else 1)
' "$WORKSPACE_MODE" "$RUN_ROOT"
}

collector_status() {
  printf '%s' "$1" | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
print(payload.get("current_evidence_collector_status", "not_running"))
'
}

describe_workspace() {
  printf '%s' "$1" | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
print(f"  Running workspace: {payload['"'"'workspace_mode'"'"']} ({payload['"'"'workspace_root'"'"']})")
'
}

web_is_qap() {
  curl -fsS --max-time 1 http://127.0.0.1:5173/ 2>/dev/null \
    | grep -q '<title>QAP Research Workbench</title>'
}

port_is_busy() {
  ss -ltnH "sport = :$1" | grep -q .
}

api_busy=0
api_qap=0
api_workspace_known=0
api_workspace_match=0
api_workspace=""
if port_is_busy 8000; then
  api_busy=1
  if api_is_qap; then
    api_qap=1
    if api_workspace="$(api_workspace_status)" \
      && workspace_status_is_valid "$api_workspace"; then
      api_workspace_known=1
      if workspace_matches_intent "$api_workspace"; then
        api_workspace_match=1
      fi
    fi
  fi
fi

web_busy=0
web_qap=0
if port_is_busy 5173; then
  web_busy=1
  if web_is_qap; then
    web_qap=1
  fi
fi

if (( api_workspace_match && web_qap )); then
  if [[ "$WORKSPACE_MODE" == "local_market" ]] \
    && [[ "$(collector_status "$api_workspace")" != "running" ]]; then
    printf 'QAP API/web are running, but the Local Market current-evidence collector is not healthy.\n' >&2
    printf 'Stop the existing workbench and relaunch it so the collector is lifecycle-managed with this workspace.\n' >&2
    exit 1
  fi
  printf 'QAP workbench is already running.\n'
  printf '  Workspace: %s (%s)\n' "$WORKSPACE_MODE" "$RUN_ROOT"
  printf '  Web: http://localhost:5173\n'
  printf '  API: http://127.0.0.1:8000\n'
  if [[ "$WORKSPACE_MODE" == "local_market" ]]; then
    printf '  Current evidence collector: running\n'
  else
    printf '  Current evidence collector: disabled in Sample Workspace\n'
  fi
  exit 0
fi

if (( api_qap && api_workspace_known && ! api_workspace_match )); then
  printf 'Cannot start QAP: another QAP workspace is already using API port 8000.\n' >&2
  describe_workspace "$api_workspace" >&2
  printf '  Intended workspace: %s (%s)\n' "$WORKSPACE_MODE" "$RUN_ROOT" >&2
  exit 1
fi

if (( api_qap && ! api_workspace_known )); then
  printf 'Cannot start QAP: a QAP API is running on port 8000, but its workspace identity cannot be verified.\n' >&2
  exit 1
fi

if (( api_workspace_match )); then
  if (( web_busy )); then
    printf 'Cannot start QAP: the intended API workspace is running, but web port 5173 is occupied by another process.\n' >&2
  else
    printf 'Cannot start QAP: the intended API workspace is running, but the QAP web app is not running.\n' >&2
  fi
  exit 1
fi

if (( web_qap )); then
  if (( api_busy )); then
    printf 'Cannot start QAP: the QAP web app is running, but API port 8000 is occupied by another process.\n' >&2
  else
    printf 'Cannot start QAP: the QAP web app is running, but the QAP API is not running.\n' >&2
  fi
  exit 1
fi

if (( api_busy || web_busy )); then
  if (( api_busy )); then
    printf 'Cannot start QAP: API port 8000 is occupied by an unrelated process.\n' >&2
  fi
  if (( web_busy )); then
    printf 'Cannot start QAP: web port 5173 is occupied by an unrelated process.\n' >&2
  fi
  exit 1
fi

api_pid=""
web_pid=""
collector_pid=""
stop_group() {
  local leader="$1"
  [[ -z "$leader" ]] && return
  kill -TERM -- "-$leader" 2>/dev/null
  for _ in {1..70}; do
    if ! kill -0 -- "-$leader" 2>/dev/null; then
      break
    fi
    sleep 0.1
  done
  if kill -0 -- "-$leader" 2>/dev/null; then
    kill -KILL -- "-$leader" 2>/dev/null
  fi
  wait "$leader" 2>/dev/null
}

cleanup() {
  trap - EXIT INT TERM
  set +e
  stop_group "$collector_pid"
  stop_group "$web_pid"
  stop_group "$api_pid"
}
trap cleanup EXIT INT TERM

QAP_API_RUN_ROOT="$RUN_ROOT" \
QAP_API_WORKSPACE_MODE="$WORKSPACE_MODE" \
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

if [[ "$WORKSPACE_MODE" == "local_market" ]]; then
  setsid bash -c '
    cd "$1"
    exec uv run python -m qap.product_current_evidence_collector "$2"
  ' _ "$ROOT" "$RUN_ROOT" &
  collector_pid=$!
fi

printf 'QAP workbench starting...\n'
printf '  Workspace: %s (%s)\n' "$WORKSPACE_MODE" "$RUN_ROOT"
printf '  Web: http://localhost:5173\n'
printf '  API: http://127.0.0.1:8000\n'
if [[ "$WORKSPACE_MODE" == "local_market" ]]; then
  printf '  Current evidence collector: enabled\n'
else
  printf '  Current evidence collector: disabled in Sample Workspace\n'
fi
printf '  Runs: %s\n' "$RUN_ROOT"
printf 'Press Ctrl+C to stop the workbench processes.\n\n'

wait -n "$api_pid" "$web_pid"
