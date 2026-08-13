from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools import check_network_expression_assurance as assurance
from tools.network_seed_reflection_oracle import PROOF_PROFILE, build_oracle
from tools.validate_repository_minimal import repository_paths

ROOT = Path(__file__).resolve().parents[1]


def oracle() -> dict:
    return build_oracle()


def transcript() -> dict:
    generated = oracle()
    responses = {}
    for case in generated["cases"]:
        actual = copy.deepcopy(case["expected"])
        final_state = copy.deepcopy(case["initial_state"])
        if actual["state_changed"]:
            observation = copy.deepcopy(case["steps"][0]["payload"]["import"])
            final_state["imports"][observation["import_id"]] = observation
        responses[case["case_id"]] = {
            "protocol": generated["implementation_protocol"]["protocol"],
            "case_id": case["case_id"],
            "actual": actual,
            "final_state": final_state,
        }
    subject = generated["historical_subject"]
    return {
        "describe": {
            "protocol": generated["implementation_protocol"]["protocol"],
            "implementation": {
                "name": "synthetic-network-expression",
                "normative": False,
                "network_canon_id": subject["canon_id"],
                "network_extension_version": subject["extension_version"],
                "network_canon_package_digest": subject["canon_package_digest"],
            },
            "operations": ["describe", "execute_case"],
        },
        "cases": responses,
    }


def proof_evidence() -> dict:
    generated = oracle()
    formal = generated["formal_oracle"]
    return {
        "profile": formal["profile"],
        "seed_release_commit": formal["seed_subject"]["release_commit"],
        "seed_resolution_sha256": formal["seed_subject"]["seed_resolution_sha256"],
        "theory_sha256": {
            key: formal[key]["sha256"] for key in ("network_model", "mapping", "proof")
        },
        "final_theorems": formal["final_theorems"],
        "obligations_proved": 1,
        "verdict": "PASS",
    }


def test_oracle_is_generated_from_tla_theory_without_checked_in_json() -> None:
    generated = oracle()
    semantics = generated["formal_oracle"]["theory_semantics"]
    assert generated["formal_oracle"]["profile"] == PROOF_PROFILE
    assert {branch["operator"] for branch in semantics["branches"]} == {
        "AdmitFresh",
        "AdmitReplay",
        "RejectConflict",
    }
    assert {case["expected"]["code"] for case in generated["cases"]} == {
        "IMPORT_ADMITTED",
        "IDEMPOTENT_REPLAY",
        "IDENTIFIER_CONFLICT",
    }
    theory_paths = [path for path in repository_paths() if path.startswith("theory/")]
    assert not any(path.endswith(".json") for path in theory_paths)


def test_checker_is_independent_from_external_python_oracles_and_implementation_imports() -> None:
    text = (ROOT / "tools/check_network_expression_assurance.py").read_text(encoding="utf-8")
    assert "reference.network_reference" not in text
    assert "aset_network_python_sqlite" not in text
    assert "importlib.import_module" not in text


def test_good_black_box_transcript_preserves_full_assurance_surface() -> None:
    report = assurance.check(ROOT, transcript=transcript(), proof_evidence=proof_evidence())
    assert report["black_box_cases"] == 4
    assert report["fresh_admission_seed_register_cases"] == 2
    assert report["replay_conflict_seed_stutter_cases"] == 2
    assert report["formal_oracle"]["proof_evidence_verified"] is True
    assert report["verdict"] == "PASS"


def test_alpha2_bound_expression_is_rejected() -> None:
    bad = transcript()
    bad["describe"]["implementation"]["network_extension_version"] = "0.1.0-alpha.2"
    with pytest.raises(ValueError, match="not bound to Network 0.1.0-alpha.3"):
        assurance.check(ROOT, transcript=bad)


def test_similar_alpha3_expression_with_wrong_package_is_rejected() -> None:
    bad = transcript()
    bad["describe"]["implementation"]["network_canon_package_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="exact Alpha3 canon package"):
        assurance.check(ROOT, transcript=bad)


def test_wrong_seed_facing_observable_is_rejected() -> None:
    bad = transcript()
    bad["cases"]["NET-POS-001"]["actual"]["semantic_status"] = "ALLOW"
    with pytest.raises(ValueError, match="black-box observable mismatch"):
        assurance.check(ROOT, transcript=bad)


def test_replay_state_change_is_rejected() -> None:
    bad = transcript()
    bad["cases"]["NET-POS-002"]["final_state"]["imports"]["imp-002"] = {"unexpected": True}
    with pytest.raises(ValueError, match="replay/conflict changed"):
        assurance.check(ROOT, transcript=bad)


def test_adapter_may_not_self_declare_conformance() -> None:
    bad = transcript()
    bad["cases"]["NET-POS-001"]["verdict"] = "PASS"
    with pytest.raises(ValueError, match="must not self-declare"):
        assurance.check(ROOT, transcript=bad)
