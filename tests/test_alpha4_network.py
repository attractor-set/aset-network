from __future__ import annotations

from pathlib import Path

from tools.alpha4_network_paired_expression import (
    bounded_pairing_check,
    operational_admit,
    parse_operational_words,
    relational_admit,
)
from tools.validate_alpha4_network import parse_binding, validate_network_surface
from tools.validate_repository_minimal import repository_paths

ROOT = Path(__file__).resolve().parents[1]


def observation(import_id: str = "i0", digest_char: str = "0") -> dict[str, str]:
    return {
        "import_id": import_id,
        "source_context": "source",
        "target_context": "target",
        "evidence_digest": "sha256:" + digest_char * 64,
    }


def test_alpha4_network_surface_is_minimal() -> None:
    validate_network_surface()
    network = (ROOT / "network/alpha4/NETWORK.aset").read_text(encoding="utf-8")
    assert "STATE IMPORTS SET-OF-EXACT-IMPORT-OBSERVATIONS" in network
    assert "TRANSITION ADMIT-IMPORT" in network
    assert "TARGET-LOCAL-SEED" in network
    assert "CAUSAL-MODEL network/alpha4/causal/components.petri" in network
    assert network.count("CAUSAL-BIND ") == 3


def test_alpha4_operational_vocabulary_is_exact() -> None:
    assert set(parse_operational_words()) == {
        "ADMIT-FRESH",
        "ADMIT-REPLAY",
        "REJECT-CONFLICT",
    }


def test_alpha4_fresh_admission_projects_unknown_without_effect() -> None:
    state, result = operational_admit([], observation())
    assert state == [observation()]
    assert result == {
        "accepted": True,
        "code": "IMPORT_ADMITTED",
        "state_changed": True,
        "seed_projection": {"recognition": "UNKNOWN", "effect_permitted": False},
    }


def test_alpha4_exact_replay_is_idempotent() -> None:
    item = observation()
    state, result = operational_admit([item], item)
    assert state == [item]
    assert result["code"] == "IDEMPOTENT_REPLAY"
    assert result["state_changed"] is False


def test_alpha4_conflicting_identifier_is_rejected() -> None:
    first = observation(digest_char="0")
    conflict = observation(digest_char="1")
    state, result = operational_admit([first], conflict)
    assert state == [first]
    assert result["accepted"] is False
    assert result["code"] == "IDENTIFIER_CONFLICT"
    assert result["seed_projection"]["effect_permitted"] is False


def test_alpha4_import_has_no_recognition_or_authority_fields() -> None:
    invalid = observation()
    invalid["recognition"] = "ALLOW"
    state, result = operational_admit([], invalid)
    assert state == []
    assert result["accepted"] is False
    assert result["code"] == "INVALID_IMPORT"


def test_alpha4_operational_and_relational_expressions_are_bounded_congruent() -> None:
    checks, accepted = bounded_pairing_check()
    assert checks == 272
    assert accepted > 0


def test_alpha4_operational_and_relational_single_case_independent() -> None:
    initial = [observation("i0", "0")]
    candidate = observation("i1", "1")
    assert operational_admit(initial, candidate) == relational_admit(initial, candidate)


def test_alpha4_seed_binding_is_content_addressed_not_commit_authority() -> None:
    sources = parse_binding()
    assert set(sources) == {
        "seed/alpha4/SEED.aset",
        "seed/alpha4/operational/components.forth",
        "seed/alpha4/formal/RestrictedOperationalSemantics.tla",
        "seed/alpha4/formal/ComponentRelations.tla",
        "seed/alpha4/formal/OperationalRelationalPairingProofs.tla",
        "seed/alpha4/formal/ComponentCompositionProofs.tla",
        "seed/alpha4/causal/components.petri",
        "theory/local-recognition/formal/LocalRecognitionAlgebra.tla",
    }
    binding = (ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset").read_text(encoding="utf-8")
    assert "CONTENT-ADDRESSED" in binding
    assert "RELEASE-TAG seed-0.4alpha-3way" in binding
    assert "REQUIRED-SEED-CAUSAL-BIND ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN" in binding
    assert (
        "ASSURANCE-BASE OPERATIONAL seed/alpha4/operational/components.forth OBSERVE-UNKNOWN"
        in binding
    )
    assert (
        "ASSURANCE-BASE RELATIONAL seed/alpha4/formal/ComponentRelations.tla ObserveUnknown"
        in binding
    )
    assert "ASSURANCE-BASE CAUSAL seed/alpha4/causal/components.petri OBSERVE-UNKNOWN" in binding
    assert "COMPANION ENGLISH en/Seed.md" in binding
    assert "COMPANION PYTHON python/aset_seed_alpha4.py" in binding
    assert "seed/alpha4/binding/graph.cddl" not in binding
    assert "COMMIT" not in binding
    assert "SEMANTIC-PRECEDENCE NONE" in binding


def test_alpha3_is_history_reference_only() -> None:
    history = (ROOT / "history/REFERENCES.aset").read_text(encoding="utf-8")
    assert "STATE NETWORK-0.1.0-ALPHA.3" in history
    assert "COMPATIBILITY ASET-NETWORK-ALPHA4 NETWORK-0.1.0-ALPHA.3 NONE" in history
    paths = repository_paths()
    assert not any(path.startswith("theory/") for path in paths)
    assert not any(path.startswith("extension/") for path in paths)
