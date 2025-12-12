import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import base64


def normalize_output(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    records = []
    for rl in data.get("resourceLogs", []):
        resource_attrs = {}
        for attr in rl.get("resource", {}).get("attributes", []):
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
            resource_attrs[attr.get("key")] = val
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
                merged = {}
                merged.update(resource_attrs)
                merged.update(attrs)
                records.append({"message": msg, "attributes": merged})
    return sorted(records, key=lambda x: x.get("message") or "")


def load_expected(dir_path: Path) -> List[Dict[str, Any]]:
    records = []
    for p in sorted(dir_path.glob("*.json")):
        records.append(json.loads(p.read_text()))
    return sorted(records, key=lambda x: x.get("message") or "")


def normalize_hec(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text()
    records = []
    try:
        payloads = json.loads(text)
    except Exception:
        payloads = []
    for entry in payloads:
        body = entry.get("body", {})
        raw_string = body.get("rawString")
        raw_bytes = body.get("rawBytes")
        json_body = body.get("json")

        if raw_bytes:
            try:
                decoded = base64.b64decode(raw_bytes).decode("utf-8", errors="replace")
                chunks = decoded.replace("}{", "}|{").split("|")
                for chunk in chunks:
                    try:
                        obj = json.loads(chunk)
                        records.append({"message": obj.get("event"), "attributes": obj.get("fields", {})})
                    except Exception:
                        records.append({"message": None, "attributes": {"raw": chunk}})
            except Exception:
                records.append({"message": None, "attributes": {"raw": raw_bytes}})
            continue

        if raw_string:
            chunks = raw_string.replace("}{", "}|{").split("|")
            for chunk in chunks:
                try:
                    obj = json.loads(chunk)
                    records.append({"message": obj.get("event"), "attributes": obj.get("fields", {})})
                except Exception:
                    records.append({"message": None, "attributes": {"raw": chunk}})
            continue

        if json_body:
            records.append({"message": json_body.get("event"), "attributes": json_body.get("fields", {})})

    return sorted(records, key=lambda x: x.get("message") or "")


def main():
    expected_dir = Path("/expected")
    otlp_file = Path("/output/logs.json")
    hec_file = Path("/output/hec.json")

    expected = load_expected(expected_dir)
    hec_records = normalize_hec(hec_file)

    if hec_records != expected:
        print("Mismatch between expected and hec records", file=sys.stderr)

        def canonicalize(records):
            out = []
            for r in records:
                key = (
                    r.get("message"),
                    json.dumps(r.get("attributes", {}), sort_keys=True, separators=(",", ":")),
                )
                out.append(key)
            return out

        exp_keys = canonicalize(expected)
        got_keys = canonicalize(hec_records)

        from collections import Counter

        missing = Counter(exp_keys) - Counter(got_keys)
        unexpected = Counter(got_keys) - Counter(exp_keys)

        if missing:
            print("Missing records:", file=sys.stderr)
            for (msg, attrs), count in missing.items():
                try:
                    attr_obj = json.loads(attrs)
                except Exception:
                    attr_obj = attrs
                sample = {"message": msg, "attributes": attr_obj}
                for _ in range(count):
                    print(json.dumps(sample, indent=2, sort_keys=True), file=sys.stderr)
        if unexpected:
            print("Unexpected records:", file=sys.stderr)
            for (msg, attrs), count in unexpected.items():
                print(f"- {count}x message='{msg}' attrs={attrs}", file=sys.stderr)

        sys.exit(1)

    print("Comparison OK (HEC only).")


if __name__ == "__main__":
    main()
