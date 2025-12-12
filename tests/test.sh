#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yaml"
EXPECTED_DIR="$ROOT_DIR/tests/expected"
OUTPUT_DIR="$ROOT_DIR/tests/output"
OUTPUT_FILE="$OUTPUT_DIR/logs.json"

# Dependency checks
command -v docker >/dev/null 2>&1 || { echo "docker not found" >&2; exit 1; }
if ! docker compose version >/dev/null 2>&1; then
  echo "'docker compose' plugin not found" >&2
  exit 1
fi
command -v jq >/dev/null 2>&1 || { echo "jq not found" >&2; exit 1; }

mkdir -p "$OUTPUT_DIR"
chmod 0777 "$OUTPUT_DIR"
rm -f "$OUTPUT_FILE"

compose_down() {
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans >/dev/null 2>&1 || true
}

emit_logs() {
  docker compose -f "$COMPOSE_FILE" logs --no-color || true
}

cleanup() {
  emit_logs
  compose_down
}
trap cleanup EXIT

# Start collector stack
compose_down
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

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

ACTUAL_TMP="$(mktemp)"
EXPECTED_TMP="$(mktemp)"

jq -c '
  .resourceLogs[].scopeLogs[].logRecords[]
  | {
      message: (.body.stringValue // .body // null),
      attributes: (
        reduce (.attributes[]? ) as $a ({}; .[$a.key] =
          ($a.value.stringValue // $a.value.intValue // $a.value.doubleValue // $a.value.boolValue // $a.value.bytesValue // $a.value.arrayValue // $a.value.kvlistValue)
        )
      )
    }
  ' "$OUTPUT_FILE" | jq -s 'sort_by(.message)' | jq -S >"$ACTUAL_TMP"
jq -s 'sort_by(.message)' "$EXPECTED_DIR"/*.json | jq -S >"$EXPECTED_TMP"

diff -u "$EXPECTED_TMP" "$ACTUAL_TMP"
echo "All tests passed."
