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

docker run --rm \
  -v "$EXPECTED_DIR":/expected:ro \
  -v "$OUTPUT_FILE":/output/logs.json:ro \
  python:3.12-slim \
  python - <<'PY'
import json
import sys
from pathlib import Path

def normalize_output(path: Path):
    data = json.loads(path.read_text())
    records = []
    for rl in data.get("resourceLogs", []):
        for sl in rl.get("scopeLogs", []):
            for lr in sl.get("logRecords", []):
                body = lr.get("body")
                msg = None
                if isinstance(body, dict):
                    msg = body.get("stringValue")
                    if msg is None and len(body) == 1:
                        msg = next(iter(body.values()))
                else:
                    msg = body
                attrs = {}
                for attr in lr.get("attributes", []):
                    v = attr.get("value", {})
                    val = (
                        v.get("stringValue")
                        if v.get("stringValue") is not None else
                        v.get("intValue")
                        if v.get("intValue") is not None else
                        v.get("doubleValue")
                        if v.get("doubleValue") is not None else
                        v.get("boolValue")
                        if v.get("boolValue") is not None else
                        v.get("bytesValue")
                        if v.get("bytesValue") is not None else
                        v.get("arrayValue")
                        if v.get("arrayValue") is not None else
                        v.get("kvlistValue")
                    )
                    attrs[attr.get("key")] = val
                records.append({"message": msg, "attributes": attrs})
    return sorted(records, key=lambda x: x.get("message") or "")

def load_expected(dir_path: Path):
    records = []
    for p in sorted(dir_path.glob("*.json")):
        records.append(json.loads(p.read_text()))
    return sorted(records, key=lambda x: x.get("message") or "")

actual = normalize_output(Path("/output/logs.json"))
expected = load_expected(Path("/expected"))

if actual != expected:
    print("Mismatch between expected and actual", file=sys.stderr)
    print("=== expected ===")
    print(json.dumps(expected, indent=2, sort_keys=True))
    print("=== actual ===")
    print(json.dumps(actual, indent=2, sort_keys=True))
    sys.exit(1)

print("Comparison OK.")
PY

echo "All tests passed."
