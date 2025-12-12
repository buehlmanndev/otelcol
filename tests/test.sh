#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yaml"
EXPECTED_DIR="$ROOT_DIR/tests/expected"
OUTPUT_DIR="$ROOT_DIR/tests/output"
OUTPUT_FILE="$OUTPUT_DIR/logs.json"
HEC_RETRIEVE="$OUTPUT_DIR/hec.json"

# Dependency checks
command -v docker >/dev/null 2>&1 || { echo "docker not found" >&2; exit 1; }
if ! docker compose version >/dev/null 2>&1; then
  echo "'docker compose' plugin not found" >&2
  exit 1
fi
command -v curl >/dev/null 2>&1 || { echo "curl not found" >&2; exit 1; }

mkdir -p "$OUTPUT_DIR"
chmod 0777 "$OUTPUT_DIR"
rm -f "$OUTPUT_FILE"
rm -f "$HEC_RETRIEVE"

compose_down() {
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans >/dev/null 2>&1 || true
}

emit_logs() {
  echo
  echo "===== otelcol container logs ====="
  docker compose -f "$COMPOSE_FILE" logs --no-color otelcol || true
  echo "===== end of otelcol logs ====="
  echo
}

cleanup() {
  emit_logs
  compose_down
}
trap cleanup EXIT

retry_curl() {
  local url=$1
  local data=$2
  local tries=10
  local delay=1
  for _ in $(seq 1 "$tries"); do
    if [ -n "$data" ]; then
      status=$(curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: application/json" -d "$data" "$url" || true)
    else
      status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    fi
    case "$status" in
      200|201) return 0 ;;
    esac
    sleep "$delay"
  done
  return 1
}

# Start stack: mockserver first, then collector after expectation
compose_down
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans hec-mock

if ! retry_curl "http://localhost:1080/mockserver/expectation" '{
  "httpRequest": { "method": "POST", "path": "/services/collector" },
  "httpResponse": { "statusCode": 200, "body": "{\"text\":\"Success\",\"code\":0}" }
}'; then
  echo "failed to configure mockserver expectation" >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" up -d --remove-orphans otelcol

# Wait for the collector to flush output
for _ in $(seq 1 20); do
  if [ -s "$OUTPUT_FILE" ]; then
    break
  fi
  sleep 1
done

if [ ! -s "$OUTPUT_FILE" ]; then
  echo "collector output not found at $OUTPUT_FILE" >&2
  exit 1
fi

# Retrieve HEC requests from mockserver
if ! retry_curl "http://localhost:1080/mockserver/retrieve" '{
  "httpRequest": { "path": "/services/collector" },
  "type": "REQUEST_RESPONSES",
  "format": "json"
}'; then
  echo "failed to retrieve from mockserver" >&2
  exit 1
fi
curl -s -X PUT "http://localhost:1080/mockserver/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
        "httpRequest": { "path": "/services/collector" },
        "type": "REQUEST_RESPONSES",
        "format": "json"
      }' >"$HEC_RETRIEVE"

if [ ! -s "$HEC_RETRIEVE" ]; then
  echo "hec retrieval empty at $HEC_RETRIEVE" >&2
  exit 1
fi

ACTUAL_TMP="$(mktemp)"
EXPECTED_TMP="$(mktemp)"

docker run --rm \
  -v "$EXPECTED_DIR":/expected:ro \
  -v "$OUTPUT_FILE":/output/logs.json:ro \
  -v "$HEC_RETRIEVE":/output/hec.json:ro \
  -v "$ROOT_DIR/tests/compare.py":/work/compare.py:ro \
  python:3.12.7-slim \
  python /work/compare.py

echo "All tests passed."
