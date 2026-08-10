from __future__ import annotations

import json
from pathlib import Path

from reference.federation_profile_reference import execute_case as execute_federation
from reference.network_reference import execute_case as execute_core
from tools.dynamic_profile_conformance import run_profile_conformance

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "extension/canonical/conformance"


def run_manifest(path, executor, label):
    profile = json.loads(path.read_text())
    failures = []
    for item in profile["cases"]:
        case = json.loads((ROOT / item["path"]).read_text())
        _, actual = executor(case)
        if actual != case["expected"]:
            failures.append((case["case_id"], case["expected"], actual))
    if failures:
        for case_id, expected, actual in failures:
            print(f"FAIL {label} {case_id}: expected={expected} actual={actual}")
        return False, len(profile["cases"])
    print(f"OK: {len(profile['cases'])} {label} conformance cases")
    return True, len(profile["cases"])


def main():
    core_ok, _ = run_manifest(C / "conformance-profile.json", execute_core, "core")
    dynamic_failures = run_profile_conformance()
    dynamic_ok = not dynamic_failures
    for case_id, expected, actual in dynamic_failures:
        print(f"FAIL dynamic-profile {case_id}: expected={expected} actual={actual}")
    if dynamic_ok:
        print("OK: dynamic-profile conformance cases")
    federation_ok, _ = run_manifest(
        C / "federation-profile-conformance-profile.json",
        execute_federation,
        "federation-profile",
    )
    return 0 if core_ok and dynamic_ok and federation_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
