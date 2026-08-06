from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reference.network_reference import execute_case

ROOT = Path(__file__).resolve().parents[1]


def test_upstream_binding_is_exact() -> None:
    binding = json.loads((ROOT / "upstream/ASET_SEED_BINDING.json").read_text(encoding="utf-8"))
    assert binding["canon_id"] == "ASET-SEED-RESOLUTION-CANON-0.2-ALPHA1"
    assert binding["compatibility"] == "STRICT_EXTENSION_NO_WEAKENING"
    assert binding["implementation_precedence"] == "NONE"


def test_model_preserves_seed_boundary() -> None:
    model = json.loads((ROOT / "extension/canonical/source/network-extension-model.json").read_text(encoding="utf-8"))
    texts = " ".join(item["text"] for item in model["invariants"])
    assert "target-local Seed" in texts
    assert "may not weaken" in texts
    assert "superior Context" in texts


def test_all_conformance_cases_match_reference_observables() -> None:
    for path in sorted((ROOT / "extension/canonical/conformance/cases").rglob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        _, actual = execute_case(case)
        assert actual == case["expected"], case["case_id"]


def test_canon_package_integrity() -> None:
    package = json.loads((ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8"))
    declared = package.pop("package_digest")
    canonical = (json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    assert declared == "sha256:" + hashlib.sha256(canonical).hexdigest()
    package["package_digest"] = declared
    assert any(item["path"] == "upstream/ASET_SEED_BINDING.json" for item in package["files"])
    for item in package["files"]:
        path = ROOT / item["path"]
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"], item["path"]


def test_import_is_never_accepted_by_observation_alone() -> None:
    case = json.loads((ROOT / "extension/canonical/conformance/cases/positive/NET-POS-005.json").read_text(encoding="utf-8"))
    state, actual = execute_case(case)
    assert actual["semantic_status"] == "UNKNOWN"
    assert actual["enforcement"] == "BLOCKED"
    assert state is not None and not state["recognitions"]
