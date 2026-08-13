from __future__ import annotations

import json
import tomllib
from pathlib import Path

from tools.validate_current_network import (
    EXPECTED_ALPHA3_BINDING_SHA256,
    EXPECTED_ALPHA3_PACKAGE_DIGEST,
    EXPECTED_ALPHA4_BINDING_SHA256,
    sha256,
    validate_current_pointer,
    validate_current_subjects,
    validate_frozen_predecessor,
    validate_project_metadata,
)

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


def test_alpha3_remains_exact_frozen_predecessor() -> None:
    validate_frozen_predecessor()
    package = json.loads((ROOT / "extension/canonical/CANON_PACKAGE.json").read_text())
    assert package["package_digest"] == EXPECTED_ALPHA3_PACKAGE_DIGEST
    assert sha256(ROOT / "upstream/ASET_SEED_BINDING.json") == EXPECTED_ALPHA3_BINDING_SHA256
    assert sha256(ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset") == EXPECTED_ALPHA4_BINDING_SHA256


def test_project_metadata_promotes_to_alpha4() -> None:
    validate_project_metadata()
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["version"] == "0.1.0a4"


def test_active_project_docs_name_alpha4_as_current_not_candidate() -> None:
    for relative in (
        "PROJECT_IDENTITY.md",
        "README.md",
        "README.ru.md",
        "README.pt-BR.md",
        "docs/ARCHITECTURE.md",
        "docs/FORMAL_VERIFICATION.md",
        "CONTRIBUTING.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "Alpha4 candidate" not in text
        assert "Alpha4-кандидат" not in text
        assert "candidato Alpha4" not in text
