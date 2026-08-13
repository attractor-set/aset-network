from __future__ import annotations

from pathlib import Path

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


def test_legacy_public_surfaces_are_absent() -> None:
    paths = repository_paths()
    for name in ("assurance", "docs", "extension", "reference"):
        assert not any(path == name or path.startswith(f"{name}/") for path in paths)


def test_retained_theory_is_not_current_semantic_authority() -> None:
    current = (ROOT / "network/CURRENT.aset").read_text(encoding="utf-8")
    profile = (ROOT / "theory/network-seed-reflection/EXPRESSION_ASSURANCE.json").read_text(
        encoding="utf-8"
    )
    assert "REFERENCE-ORACLE-AUTHORITY NONE" in current
    assert '"normative": false' in profile
    assert '"normative_precedence": "NONE"' in profile
