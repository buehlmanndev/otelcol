import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def normalize_output(path: Path) -> List[Dict[str, Any]]:
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
                        if v.get("stringValue") is not None
                        else v.get("intValue")
                        if v.get("intValue") is not None
                        else v.get("doubleValue")
                        if v.get("doubleValue") is not None
                        else v.get("boolValue")
                        if v.get("boolValue") is not None
                        else v.get("bytesValue")
                        if v.get("bytesValue") is not None
                        else v.get("arrayValue")
                        if v.get("arrayValue") is not None
                        else v.get("kvlistValue")
                    )
                    attrs[attr.get("key")] = val
                records.append({"message": msg, "attributes": attrs})
    return sorted(records, key=lambda x: x.get("message") or "")


def load_expected(dir_path: Path) -> List[Dict[str, Any]]:
    records = []
    for p in sorted(dir_path.glob("*.json")):
        records.append(json.loads(p.read_text()))
    return sorted(records, key=lambda x: x.get("message") or "")


def normalize_hec(path: Path) -> List[Dict[str, Any]]:
    records = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        records.append({"message": obj.get("event"), "attributes": obj.get("fields", {})})
    return sorted(records, key=lambda x: x.get("message") or "")


def main():
    expected_dir = Path("/expected")
    otlp_file = Path("/output/logs.json")
    hec_file = Path("/output/hec.ndjson")

    expected = load_expected(expected_dir)
    actual = normalize_output(otlp_file)
    hec_records = normalize_hec(hec_file)

    if actual != expected:
        print("Mismatch between expected and actual", file=sys.stderr)
        print("=== expected ===")
        print(json.dumps(expected, indent=2, sort_keys=True))
        print("=== actual ===")
        print(json.dumps(actual, indent=2, sort_keys=True))
        sys.exit(1)

    if hec_records != expected:
        print("Mismatch between expected and hec records", file=sys.stderr)
        print("=== expected ===")
        print(json.dumps(expected, indent=2, sort_keys=True))
        print("=== hec ===")
        print(json.dumps(hec_records, indent=2, sort_keys=True))
        sys.exit(1)

    print("Comparison OK.")


if __name__ == "__main__":
    main()
