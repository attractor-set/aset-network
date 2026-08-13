from __future__ import annotations

from pathlib import Path

from tools.validate_repository_minimal import (
    repository_paths,
    validate_active_network_line,
    validate_attribution,
    validate_history_surface,
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
    validate_history_surface()
    validate_upstream_surface()
    validate_verification_surface()
    validate_attribution()


def test_history_is_reference_only_and_legacy_executable_surface_is_absent() -> None:
    paths = repository_paths()
    assert not any(path.startswith("theory/") for path in paths)
    assert not any(path.startswith("extension/") for path in paths)
    history = (ROOT / "history/REFERENCES.aset").read_text(encoding="utf-8")
    assert "STATE NETWORK-0.1.0-ALPHA.3" in history
    assert "MECHANICALLY_PROVED" in history
    active = (ROOT / "network/alpha4/NETWORK.aset").read_text(encoding="utf-8")
    assert "history/" not in active
    assert "theory/" not in active
