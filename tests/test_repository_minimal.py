from __future__ import annotations

from pathlib import Path

from tools.network_seed_reflection_oracle import build_oracle
from tools.validate_repository_minimal import (
    repository_paths,
    validate_active_network_line,
    validate_attribution,
    validate_history_and_theory,
    validate_root_surface,
    validate_single_readme,
    validate_upstream_surface,
    validate_verification_surface,
)

ROOT = Path(__file__).resolve().parents[1]


def test_repository_surface_is_seed_style_minimal() -> None:
    validate_root_surface()
    validate_single_readme()
    validate_active_network_line()
    validate_history_and_theory()
    validate_upstream_surface()
    validate_verification_surface()
    validate_attribution()


def test_theory_contains_only_tla_sources_and_is_not_current_semantic_authority() -> None:
    paths = repository_paths()
    theory = sorted(path for path in paths if path.startswith("theory/network-seed-reflection/"))
    assert theory == [
        "theory/network-seed-reflection/formal/NetworkExtension.tla",
        "theory/network-seed-reflection/formal/NetworkExtensionSeedRefinement.tla",
        "theory/network-seed-reflection/formal/NetworkExtensionSeedRefinementProofs.tla",
    ]
    assert "network/CURRENT.aset" not in paths
    assert not any(path.endswith(".json") for path in theory)
    active = (ROOT / "network/alpha4/NETWORK.aset").read_text(encoding="utf-8")
    assert "theory/network-seed-reflection" not in active
    oracle = build_oracle()
    assert oracle["schema_version"] == 4
    assert oracle["normative"] is False
    assert oracle["normative_precedence"] == "NONE"
    assert oracle["implementation_protocol"]["implementation_imports"] == "NONE"
    assert oracle["implementation_protocol"]["self_declared_conformance"] == "ABSENT"
