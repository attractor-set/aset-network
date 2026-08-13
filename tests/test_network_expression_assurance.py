from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "check_network_expression_assurance.py"
SPEC = importlib.util.spec_from_file_location("network_expression_assurance", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def profile() -> dict:
    return json.loads(
        (ROOT / "assurance/expression-independent/ASSURANCE_PROFILE.json").read_text(
            encoding="utf-8"
        )
    )


def transcript() -> dict:
    p = profile()
    conformance = json.loads(
        (ROOT / p["subject"]["conformance_profile"]).read_text(encoding="utf-8")
    )
    responses = {}
    for entry in conformance["cases"]:
        case = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        actual = copy.deepcopy(entry["expected"])
        final_state = copy.deepcopy(case["initial_state"])
        if actual["state_changed"]:
            observation = copy.deepcopy(case["steps"][0]["payload"]["import"])
            final_state["imports"][observation["import_id"]] = observation
        responses[case["case_id"]] = {
            "protocol": p["implementation_protocol"]["protocol"],
            "case_id": case["case_id"],
            "actual": actual,
            "final_state": final_state,
        }
    return {
        "describe": {
            "protocol": p["implementation_protocol"]["protocol"],
            "implementation": {
                "name": "aset-network-python-sqlite",
                "normative": False,
                "network_canon_id": p["subject"]["canon_id"],
                "network_extension_version": p["subject"]["extension_version"],
            },
            "operations": ["describe", "execute_case"],
        },
        "cases": responses,
    }


def test_profile_pins_frozen_mechanically_proved_oracle() -> None:
    p = profile()
    assert p["formal_oracle"]["profile"] == "ASET-NETWORK-SEED-REFINEMENT-TLAPS-V2"
    assert p["formal_oracle"]["status"] == "MECHANICALLY_PROVED"
    assert p["formal_oracle"]["obligations_proved"] == 35
    assert set(p["formal_oracle"]["final_theorems"]) == {
        "NetworkExtensionRefinesSeedSafetySpec",
        "NetworkProjectionMatchesSeedResolution",
    }


def test_checker_is_independent_from_python_oracles_and_implementation_imports() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "reference.network_reference" not in text
    assert "aset_network_python_sqlite" not in text
    assert "importlib.import_module" not in text


def test_good_black_box_transcript_commutes_with_seed_oracle() -> None:
    report = MODULE.check(ROOT, transcript=transcript())
    assert report["black_box_cases"] == 4
    assert report["fresh_admission_seed_oracle_cases"] == 2
    assert report["verdict"] == "PASS"


def test_alpha2_bound_expression_is_rejected() -> None:
    bad = transcript()
    bad["describe"]["implementation"]["network_extension_version"] = "0.1.0-alpha.2"
    with pytest.raises(ValueError, match="not bound to Network 0.1.0-alpha.3"):
        MODULE.check(ROOT, transcript=bad)


def test_wrong_seed_facing_observable_is_rejected() -> None:
    bad = transcript()
    bad["cases"]["NET-POS-001"]["actual"]["semantic_status"] = "ALLOW"
    with pytest.raises(ValueError, match="black-box observable mismatch"):
        MODULE.check(ROOT, transcript=bad)


def test_adapter_may_not_self_declare_conformance() -> None:
    bad = transcript()
    bad["cases"]["NET-POS-001"]["verdict"] = "PASS"
    with pytest.raises(ValueError, match="self-declares"):
        MODULE.check(ROOT, transcript=bad)
