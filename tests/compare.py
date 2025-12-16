import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import base64


def normalize_output(path: Path) -> List[Dict[str, Any]]:
    # Unused in current flow, kept for completeness
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


def load_expected(dir_path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    records: List[Tuple[str, Dict[str, Any]]] = []
    for p in sorted(dir_path.glob("*.json")):
        records.append((p.name, json.loads(p.read_text())))
    # sort by message for stable pairing
    return sorted(records, key=lambda x: x[1].get("message") or "")


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


def diff_attrs(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    diffs = []
    for k, v in expected.items():
        if k not in actual:
            diffs.append(f"missing attr '{k}'")
        elif actual[k] != v:
            diffs.append(f"attr '{k}' expected '{v}' got '{actual[k]}'")
    for k in actual:
        if k not in expected:
            diffs.append(f"unexpected attr '{k}'")
    return diffs


def main():
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"

    expected_dir = Path("/expected")
    hec_file = Path("/output/hec.json")
    results_dir = Path("/output/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    expected = load_expected(expected_dir)
    hec_records = normalize_hec(hec_file)

    # Align by sorted message for deterministic pairing
    exp_sorted = sorted(expected, key=lambda x: x[1].get("message") or "")
    act_sorted = sorted(hec_records, key=lambda x: x.get("message") or "")

    status_ok = True
    pass_count = 0
    fail_count = 0
    if len(exp_sorted) != len(act_sorted):
        print(f"{RED}FAIL{RESET} length mismatch: expected {len(exp_sorted)} got {len(act_sorted)}", file=sys.stderr)
        status_ok = False

    for idx, (exp_item, act_item) in enumerate(zip(exp_sorted, act_sorted)):
        filename, exp_record = exp_item
        act_record = act_item
        # Persist actual in expectation format for diff-by-eye
        out_path = results_dir / f"{filename}.actual.json"
        out_path.write_text(json.dumps(act_record, indent=2, sort_keys=True))

        diffs = []
        if exp_record.get("message") != act_record.get("message"):
            diffs.append("message differs")
        diffs.extend(diff_attrs(exp_record.get("attributes", {}), act_record.get("attributes", {})))

        if diffs:
            print(f"{RED}FAIL{RESET} {filename}: " + "; ".join(diffs), file=sys.stderr)
            status_ok = False
            fail_count += 1
        else:
            print(f"{GREEN}PASS{RESET} {filename}")
            pass_count += 1

    if not status_ok:
        print(f"\nSummary: {pass_count} passed, {fail_count} failed.", file=sys.stderr)
        print(f"Actual results saved under {results_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{GREEN}All comparisons passed.{RESET}")
    print(f"Results (actuals) saved under {results_dir}")


if __name__ == "__main__":
    main()
