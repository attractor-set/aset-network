from __future__ import annotations

from pathlib import Path

from tools.alpha4_network_paired_expression import (
    bounded_pairing_check,
    operational_admit,
    parse_operational_words,
    relational_admit,
)
from tools.validate_alpha4_network import parse_binding, validate_network_surface

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
    assert len(sources) == 8
    binding = (ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset").read_text(encoding="utf-8")
    assert "CONTENT-ADDRESSED" in binding
    assert "COMMIT" not in binding
    assert "SEMANTIC-PRECEDENCE NONE" in binding


def test_alpha3_canon_remains_frozen_predecessor() -> None:
    package = (ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8")
    assert '"canon_id": "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3"' in package
    assert (
        '"package_digest": '
        '"sha256:82976c30880ed2a6c810b8f0aa5585dee5ab73fa12684a9d17784bac0a1bbbc7"'
    ) in package
