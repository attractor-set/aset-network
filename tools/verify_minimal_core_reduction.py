from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from reference.legacy_network_reference import apply_transition
from tools.dynamic_profile_conformance import validate_wire_object

ROOT = Path(__file__).resolve().parents[1]


CANON = ROOT / "extension/canonical"
REDUCTION = CANON / "assurance/minimal-core-reduction.json"
FED = CANON / "protocol/federation-profile.json"
FED_DEF = CANON / "protocol/profiles/federation-profile-definition.json"
LEGACY = CANON / "conformance/legacy-alpha2-cases"


def project(state: dict[str, Any] | None) -> dict[str, Any]:
    return {"imports": copy.deepcopy((state or {}).get("imports", {}))}


def verify_profile_definition() -> None:
    definition = json.loads(FED_DEF.read_text())
    ok, code = validate_wire_object("PROFILE_DEFINITION", definition)
    if not ok:
        raise SystemExit(f"federation profile definition invalid: {code}")


def verify_decomposition() -> None:
    reduction = json.loads(REDUCTION.read_text())
    federation = json.loads(FED.read_text())
    if reduction["normative_core"]["semantic_state_fields"] != ["imports"] or reduction[
        "normative_core"
    ]["transition_kinds"] != ["ADMIT_IMPORT"]:
        raise SystemExit("normative minimal core is not imports + ADMIT_IMPORT")
    if reduction.get("normative") is not True or reduction.get("status") != (
        "NORMATIVE_CUTOVER_ALPHA3"
    ):
        raise SystemExit("minimal-core reduction is not normative cutover")

    extraction = federation["extraction_semantics"]
    if (
        extraction["normative_core_changed_by_this_slice"] is not True
        or extraction["phase"] != "NORMATIVE_PROFILE_AFTER_CORE_CUTOVER"
    ):
        raise SystemExit("federation profile is not post-cutover")
    if extraction["network_admission_state_retained"] != ["imports"] or extraction[
        "seed_derived_legacy_state_fields"
    ] != ["recognitions"]:
        raise SystemExit("federation cutover ownership mismatch")


def verify_conformance_trace_projection() -> int:
    reduction = json.loads(REDUCTION.read_text())
    federation_transitions = set(reduction["decomposition"]["federation_profile_transition_kinds"])
    seed_transitions = set(reduction["decomposition"]["seed_derived_transition_kinds"])
    count = 0
    success = 0
    for path in sorted(LEGACY.rglob("*.json")):
        case = json.loads(path.read_text())
        state = copy.deepcopy(case["initial_state"])
        for transition in case["steps"]:
            before = project(state)
            state, result = apply_transition(state, transition)
            after = project(state)
            kind = transition["kind"]
            if kind == "OBSERVE_IMPORT":
                if result["accepted"] and result["state_changed"]:
                    if len(set(after["imports"]) - set(before["imports"])) != 1:
                        raise SystemExit(f"{case['case_id']}: admission projection not append")
                    success += 1
                elif after != before:
                    raise SystemExit(
                        f"{case['case_id']}: rejected/replay observe changed projection"
                    )
            elif kind in federation_transitions or kind in seed_transitions:
                if after != before:
                    raise SystemExit(f"{case['case_id']}: {kind} must stutter")
            else:
                raise SystemExit(f"{case['case_id']}: unclassified legacy transition {kind}")
            if not result["accepted"]:
                break
        count += 1

    if success == 0:
        raise SystemExit("legacy traces exercised no successful admission")
    return count


def main() -> int:
    verify_profile_definition()
    verify_decomposition()
    count = verify_conformance_trace_projection()
    print("OK: federation profile definition is valid dynamic-profile evidence")
    print("OK: normative minimal core state_fields=1 transition_kinds=1")
    print(f"OK: legacy reduction conformance traces={count}")
    print("OK: federation/Seed-derived legacy transitions stutter under admission projection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
