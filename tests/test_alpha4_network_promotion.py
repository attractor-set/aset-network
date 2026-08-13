from __future__ import annotations

from pathlib import Path

from tools.validate_current_network import (
    EXPECTED_ALPHA3_PACKAGE_DIGEST,
    EXPECTED_ALPHA3_RELEASE_COMMIT,
    EXPECTED_ALPHA4_BINDING_SHA256,
    sha256,
    validate_current_pointer,
    validate_current_subjects,
    validate_history_boundary,
    validate_project_identity,
)
from tools.validate_repository_minimal import repository_paths

ROOT = Path(__file__).resolve().parents[1]


def test_alpha4_is_current_project_representation() -> None:
    validate_current_pointer()
    current = (ROOT / "network/CURRENT.aset").read_text(encoding="utf-8")
    assert "CURRENT-REPRESENTATION network/alpha4/NETWORK.aset" in current
    assert "CURRENT-PROFILES network/alpha4/profiles/PROFILES.aset" in current
    assert "PROMOTION-SEMANTIC-DELTA NONE" in current


def test_promotion_does_not_grant_semantic_precedence() -> None:
    validate_current_subjects()
    current = (ROOT / "network/CURRENT.aset").read_text(encoding="utf-8")
    network = (ROOT / "network/alpha4/NETWORK.aset").read_text(encoding="utf-8")
    profiles = (ROOT / "network/alpha4/profiles/PROFILES.aset").read_text(encoding="utf-8")
    assert "SEMANTIC-PRECEDENCE NONE" in current
    assert "SEMANTIC-PRECEDENCE NONE" in network
    assert "SEMANTIC-PRECEDENCE NONE" in profiles


def test_alpha3_is_historical_reference_not_active_semantic_surface() -> None:
    validate_history_boundary()
    history = (ROOT / "history/REFERENCES.aset").read_text(encoding="utf-8")
    assert f"COMMIT {EXPECTED_ALPHA3_RELEASE_COMMIT}" in history
    assert f"CANON-PACKAGE {EXPECTED_ALPHA3_PACKAGE_DIGEST}" in history
    paths = repository_paths()
    assert not any(path.startswith("extension/") for path in paths)
    assert "upstream/ASET_SEED_BINDING.json" not in paths
    assert sha256(ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset") == EXPECTED_ALPHA4_BINDING_SHA256


def test_project_identity_is_seed_style_citation_and_notice() -> None:
    validate_project_identity()
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert 'version: "0.1.0-alpha.4"' in citation
    assert "Dzmitry Prychyna" in notice
    assert "Attractor Set" in notice


def test_single_active_readme_names_alpha4_as_current() -> None:
    readmes = sorted(
        path for path in repository_paths() if Path(path).name.lower().startswith("readme")
    )
    assert readmes == ["README.md"]
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "0.1.0-alpha.4 is the current public representation" in text
    assert "candidate" not in text.lower()
