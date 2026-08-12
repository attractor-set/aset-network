from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "check_seed_projection_assurance.py"
SPEC = importlib.util.spec_from_file_location("seed_projection_assurance", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_profile_is_non_normative() -> None:
    profile = json.loads(
        (ROOT / "assurance/seed-projection/ASSURANCE_PROFILE.json").read_text(encoding="utf-8")
    )
    assert profile["normative"] is False
    assert profile["normative_precedence"] == "NONE"
    assert profile["relation_type"] == "EVIDENCE_COMPOSITION_OVER_SHARED_SEED_SUBJECT"


def test_profile_pins_shared_seed_and_public_v60() -> None:
    profile = json.loads(
        (ROOT / "assurance/seed-projection/ASSURANCE_PROFILE.json").read_text(encoding="utf-8")
    )
    assert profile["shared_seed_subject"]["seed_resolution_sha256"] == (
        "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
    )
    assert profile["public_v60_subject"]["package_digest"] == (
        "sha256:d537ad0555a0746e297f309e841aaccc8f059a44177400fd155253037a31747c"
    )
    assert profile["public_v60_subject"]["expected_tlaps_obligations"] == 2257


def test_profile_does_not_claim_new_mechanical_composition() -> None:
    profile = json.loads(
        (ROOT / "assurance/seed-projection/ASSURANCE_PROFILE.json").read_text(encoding="utf-8")
    )
    excluded = profile["claim_boundary"]["excluded"]
    assert "a new mechanically composed Network-to-v60 TLAPS theorem" in excluded


def test_projection_contract_keeps_terminal_recognition_outside_network() -> None:
    profile = json.loads(
        (ROOT / "assurance/seed-projection/ASSURANCE_PROFILE.json").read_text(encoding="utf-8")
    )
    contract = profile["projection_contract"]
    assert contract["admitted_effective_resolution"] == "UNKNOWN"
    assert contract["admitted_effect_permitted"] is False
    assert contract["network_owned_terminal_recognition"] is False
