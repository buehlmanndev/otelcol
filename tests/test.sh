#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yaml"
EXPECTED_DIR="$ROOT_DIR/tests/expected"
OUTPUT_DIR="$ROOT_DIR/tests/output"
OUTPUT_FILE="$OUTPUT_DIR/logs.json"
HEC_FILE="$OUTPUT_DIR/hec.ndjson"

# Dependency checks
command -v docker >/dev/null 2>&1 || { echo "docker not found" >&2; exit 1; }
if ! docker compose version >/dev/null 2>&1; then
  echo "'docker compose' plugin not found" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
chmod 0777 "$OUTPUT_DIR"
rm -f "$OUTPUT_FILE"
rm -f "$HEC_FILE"

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
if [ ! -s "$HEC_FILE" ]; then
  echo "hec output not found at $HEC_FILE" >&2
  exit 1
fi

ACTUAL_TMP="$(mktemp)"
EXPECTED_TMP="$(mktemp)"

docker run --rm \
  -v "$EXPECTED_DIR":/expected:ro \
  -v "$OUTPUT_FILE":/output/logs.json:ro \
  -v "$HEC_FILE":/output/hec.ndjson:ro \
  -v "$ROOT_DIR/tests/compare.py":/work/compare.py:ro \
  python:3.12-slim \
  python /work/compare.py

echo "All tests passed."
