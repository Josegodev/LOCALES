#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"
START_BACKEND="${START_BACKEND:-1}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8011}"
BASE_URL="${BASE_URL:-http://${HOST}:${PORT}}"
ENDPOINT="${BASE_URL%/}/api/evals/chat/run"
HEALTH_URL="${BASE_URL%/}/health"
TMP_BODY="$(mktemp)"
TMP_LOG="$(mktemp)"
BACKEND_PID=""

cleanup() {
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -f "$TMP_BODY" "$TMP_LOG"
}

wait_for_health() {
  local attempts=40
  local attempt=1
  while (( attempt <= attempts )); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
    attempt=$((attempt + 1))
  done
  return 1
}

trap cleanup EXIT

if [[ "$START_BACKEND" == "1" ]]; then
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python no encontrado en $PYTHON_BIN" >&2
    exit 1
  fi
  echo "Starting isolated backend from ${REPO_ROOT} on ${BASE_URL}"
  (
    cd "$REPO_ROOT"
    exec "$PYTHON_BIN" -m uvicorn app.main:app --host "$HOST" --port "$PORT"
  ) >"$TMP_LOG" 2>&1 &
  BACKEND_PID="$!"
  if ! wait_for_health; then
    echo "Backend no arranca en ${HEALTH_URL}" >&2
    cat "$TMP_LOG" >&2
    exit 1
  fi
else
  echo "Checking backend health at ${HEALTH_URL}"
  curl -fsS "$HEALTH_URL" >/dev/null
fi

echo "Running chat evals through ${ENDPOINT}"
HTTP_CODE="$(
  curl -sS \
    -o "$TMP_BODY" \
    -w "%{http_code}" \
    -X POST \
    "${ENDPOINT}"
)"

python3 - "$TMP_BODY" "$HTTP_CODE" <<'PY'
import json
import sys
from pathlib import Path

body_path = Path(sys.argv[1])
http_code = int(sys.argv[2])
raw = body_path.read_text(encoding="utf-8")

try:
    payload = json.loads(raw) if raw else {}
except json.JSONDecodeError as exc:
    print(f"Invalid JSON from backend (HTTP {http_code}): {exc}", file=sys.stderr)
    if raw:
        print(raw, file=sys.stderr)
    raise SystemExit(1)

if http_code != 200:
    print(f"Eval endpoint failed with HTTP {http_code}", file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=True, indent=2), file=sys.stderr)
    raise SystemExit(1)

summary = payload.get("summary") or {}
print("status:", payload.get("status", "unknown"))
print("run_id:", payload.get("run_id", "-"))
print("run_path:", payload.get("run_path", "-"))
print(
    "summary:",
    f"total={summary.get('total', '-')}",
    f"passed={summary.get('passed', '-')}",
    f"failed={summary.get('failed', '-')}",
    f"errors={summary.get('errors', '-')}",
    f"pass_rate={summary.get('pass_rate', '-')}",
)

failed_results = [
    item for item in payload.get("results", [])
    if isinstance(item, dict) and item.get("passed") is False
]
if failed_results:
    print("failures:")
    for item in failed_results:
        print(f"- {item.get('case_id', '-')}: {item.get('failures', [])}")
PY
