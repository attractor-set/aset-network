from __future__ import annotations

from pathlib import Path

from tools.alpha4_network_profiles_gate import (
    FEDERATION_CAPABILITIES,
    FEDERATION_STATES,
    FEDERATION_TRANSITIONS,
    bounded_federation_check,
    lines,
    validate_composition,
    validate_dynamic,
    validate_federation_surface,
    validate_liveness,
    validate_registry,
    values,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "network/alpha4/profiles"


def test_alpha4_profile_registry_is_separate_from_core_subject() -> None:
    validate_registry()
    core = (ROOT / "network/alpha4/NETWORK.aset").read_text(encoding="utf-8")
    assert "profiles/" not in core
    registry = (PROFILES / "PROFILES.aset").read_text(encoding="utf-8")
    assert "PARENT-SUBJECT network/alpha4/NETWORK.aset" in registry
    assert "INVARIANT PROFILE-OPERATIONAL-RELATIONAL-PAIRING REQUIRED" in registry
    assert "INVARIANT OPERATIONAL-EXPRESSION-SUBJECT SEMANTIC-OBJECT" in registry
    assert "INVARIANT OPERATIONAL-EXPRESSION-REQUIRES-STATE NEVER" in registry
    assert "INVARIANT OPERATIONAL-EXPRESSION-REQUIRES-TRANSITION NEVER" in registry


def test_alpha4_dynamic_profile_adds_no_network_state_or_transition() -> None:
    checks, applicable = validate_dynamic()
    assert checks == 6
    assert applicable == 1


def test_operational_expression_is_independent_of_state_and_transition_ownership() -> None:
    dynamic = lines(PROFILES / "dynamic/DYNAMIC.aset")
    liveness = lines(PROFILES / "liveness/LIVENESS.aset")

    for profile in (dynamic, liveness):
        assert "STATE-ADDED NONE" in profile
        assert "TRANSITION-ADDED NONE" in profile
        assert any(line.startswith("OPERATIONAL ") for line in profile)


def test_alpha4_federation_owns_exact_profile_surface() -> None:
    validate_federation_surface()
    path = PROFILES / "federation/FEDERATION.aset"
    assert set(values(path, "STATE")) == FEDERATION_STATES
    assert set(values(path, "TRANSITION")) == FEDERATION_TRANSITIONS
    assert set(values(path, "CAPABILITY")) == FEDERATION_CAPABILITIES


def test_alpha4_federation_bounded_lifecycle_preserves_invariants() -> None:
    states, edges = bounded_federation_check()
    assert states > 10
    assert edges > states


def test_alpha4_federation_profile_declares_network_stuttering() -> None:
    federation = lines(PROFILES / "federation/FEDERATION.aset")
    assert "INVARIANT NETWORK-IMPORTS-STUTTER-ON-PROFILE-TRANSITION" in federation
    assert "INVARIANT AUTHORITY-INHERITANCE NEVER" in federation


def test_alpha4_liveness_is_property_only_and_does_not_require_allow() -> None:
    validate_liveness()
    liveness = lines(PROFILES / "liveness/LIVENESS.aset")
    assert "STATE-ADDED NONE" in liveness
    assert "TRANSITION-ADDED NONE" in liveness
    assert "EVENTUAL-ALLOW-REQUIRED FALSE" in liveness


def test_alpha4_liveness_terminal_results_remain_seed_owned() -> None:
    path = PROFILES / "liveness/LIVENESS.aset"
    assert set(values(path, "SEED-TERMINAL-RESULT")) == {"ALLOW", "BLOCK"}
    assert "SEED-RESOLUTION-OWNER TARGET-LOCAL-SEED" in lines(path)


def test_alpha4_federation_liveness_composition_transfers_no_ownership() -> None:
    validate_composition()
    composition = lines(PROFILES / "composition/federation-liveness/FEDERATION_LIVENESS.aset")
    assert "PROFILE-PARENT-RELATION FALSE" in composition
    assert "STATE-OWNERSHIP-TRANSFER NONE" in composition
    assert "TRANSITION-OWNERSHIP-TRANSFER NONE" in composition
    assert "AUTHORITY-TRANSFER NONE" in composition


def test_alpha4_profile_surface_does_not_name_python_oracles() -> None:
    for path in PROFILES.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "reference/" not in text
            assert "python-sqlite" not in text


def test_alpha3_profile_surface_remains_present_as_frozen_predecessor() -> None:
    alpha3 = ROOT / "extension/canonical/profiles"
    assert (alpha3 / "dynamic/profile.json").is_file()
    assert (alpha3 / "federation/profile.json").is_file()
    assert (alpha3 / "liveness/profile.json").is_file()
