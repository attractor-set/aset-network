from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reference.network_reference import execute_case


def main() -> int:
    failures = []
    paths = sorted((ROOT / "extension/canonical/conformance/cases").rglob("*.json"))
    for path in paths:
        case = json.loads(path.read_text(encoding="utf-8"))
        _, actual = execute_case(case)
        if actual != case["expected"]:
            failures.append((case["case_id"], case["expected"], actual))
    if failures:
        for case_id, expected, actual in failures:
            print(f"FAIL: {case_id}\n expected={expected}\n actual={actual}")
        return 1
    print(f"OK: {len(paths)} conformance cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
