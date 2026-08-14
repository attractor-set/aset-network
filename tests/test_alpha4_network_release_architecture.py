from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools import run_alpha4_network_release_tlaps as release_tlaps
from tools.alpha4_network_release_admission import archive_tree_digest
from tools.alpha4_network_release_profiles import (
    _manifest_records,
    parse_english,
    write_english,
    write_python,
)
from tools.alpha4_network_seed_extension import SeedBinding, tree_digest
from tools.build_alpha4_network_release import write_assembled_network, zip_tree


def test_release_companion_surface_is_downstream_of_three_way_assurance(tmp_path: Path) -> None:
    records = _manifest_records()
    assert len(records) == 21
    assert {item["subject"] for item in records} == {
        "NETWORK",
        "DYNAMIC",
        "FEDERATION",
        "LIVENESS",
        "FEDERATION-LIVENESS",
    }
    english = tmp_path / "Network.md"
    write_english(english, "sha256:" + "1" * 64, records)
    parsed = parse_english(english)
    assert [item["component_id"] for item in parsed] == [item["component_id"] for item in records]
    assert all(item["seed_extension"] == "NONE" for item in records if item["subject"] != "NETWORK")
    assert [item["seed_extension"] for item in records if item["subject"] == "NETWORK"] == [
        "OBSERVE-UNKNOWN",
        "OBSERVE-UNKNOWN",
        "NONE",
    ]


def test_generated_network_python_composes_exact_seed_python_base(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    base = profiles / "base/seed/python/aset_seed_alpha4.py"
    target = profiles / "python/aset_network_alpha4.py"
    base.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    base.write_text(
        "def state(subject, authority, recognition='UNKNOWN', evidence=()):\n"
        "    return {'subject': subject, 'authority': authority, "
        "'recognition': recognition, 'evidence': tuple(evidence)}\n"
        "def apply_component(current, component_id, *, evidence=None, "
        "authority_recognition=frozenset()):\n"
        "    if component_id != 'ASET-COMPONENT-OBSERVE-UNKNOWN': raise ValueError('component')\n"
        "    if current['recognition'] != 'UNKNOWN': raise ValueError('recognition')\n"
        "    result = dict(current); result['evidence'] = "
        "tuple(sorted(set(current['evidence']) | {evidence})); return result\n",
        encoding="utf-8",
    )
    digest = "sha256:" + hashlib.sha256(base.read_bytes()).hexdigest()
    write_python(target, digest, _manifest_records())
    generated = target.read_text(encoding="utf-8")
    assert "def state(" not in generated
    assert "def apply_component" not in generated
    assert '_seed["apply_component"]' in generated
    assert "ASET-COMPONENT-OBSERVE-UNKNOWN" in generated
    namespace = {"__file__": str(target)}
    exec(compile(target.read_text(encoding="utf-8"), str(target), "exec"), namespace)
    seed_state = namespace["_seed"]["state"]("subject", "authority")
    observation = {
        "import_id": "i0",
        "source_context": "source",
        "target_context": "target",
        "evidence_digest": "sha256:" + "0" * 64,
    }
    imports, result_seed, result = namespace["admit_import"]([], observation, seed_state)
    assert imports == [observation]
    assert result["accepted"] is True
    assert result["seed_projection"]["component"] == "ASET-COMPONENT-OBSERVE-UNKNOWN"
    assert result_seed["recognition"] == "UNKNOWN"
    assert observation["evidence_digest"] in result_seed["evidence"]


def test_generated_network_python_rejects_tampered_seed_base(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    base = profiles / "base/seed/python/aset_seed_alpha4.py"
    target = profiles / "python/aset_network_alpha4.py"
    base.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    base.write_text("def state(*args, **kwargs): return {}\n", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(base.read_bytes()).hexdigest()
    write_python(target, digest, _manifest_records())
    base.write_text(base.read_text(encoding="utf-8") + "# tampered\n", encoding="utf-8")
    namespace = {"__file__": str(target)}
    try:
        exec(compile(target.read_text(encoding="utf-8"), str(target), "exec"), namespace)
    except RuntimeError as error:
        assert "exact Seed Python companion byte identity mismatch" in str(error)
    else:
        raise AssertionError("tampered Seed Python base was accepted")


def test_assembled_network_materialization_is_core_only_and_non_semantic(tmp_path: Path) -> None:
    target = tmp_path / "AssembledNetwork.tla"
    write_assembled_network(target)
    text = target.read_text(encoding="utf-8")
    assert "MODULE AssembledNetwork" in text
    assert "EXTENDS NetworkRelations" in text
    assert "Next(s, t, observation, result)" in text
    assert "AdmitImport(s, t, observation, result)" in text
    assert "ALLOW" not in text
    assert "BLOCK" not in text


def test_release_archive_digest_is_exact_tree_identity(tmp_path: Path) -> None:
    tree = tmp_path / "ASET-Network-test"
    (tree / "nested").mkdir(parents=True)
    (tree / "a.txt").write_text("a\n", encoding="utf-8")
    (tree / "nested/b.txt").write_text("b\n", encoding="utf-8")
    archive = tmp_path / "release.zip"
    zip_tree(tree, archive, tree.name)
    digest, paths = archive_tree_digest(archive, tree.name)
    assert digest == tree_digest(tree)
    assert paths == {"a.txt", "nested/b.txt"}


def test_post_build_verifier_is_isolated_and_bound_to_exact_seed_relation(
    tmp_path: Path, monkeypatch
) -> None:
    release = tmp_path / "release"
    seed = tmp_path / "seed"
    (release / "formal").mkdir(parents=True)
    (release / "network/alpha4/formal").mkdir(parents=True)
    (seed / "formal").mkdir(parents=True)
    write_assembled_network(release / "formal/AssembledNetwork.tla")
    (release / "network/alpha4/formal/NetworkRelations.tla").write_text(
        "---- MODULE NetworkRelations ----\n====\n", encoding="utf-8"
    )
    component = seed / "formal/ComponentRelations.tla"
    component.write_text("---- MODULE ComponentRelations ----\n====\n", encoding="utf-8")
    (seed / "formal/LocalRecognitionAlgebra.tla").write_text(
        "---- MODULE LocalRecognitionAlgebra ----\n====\n", encoding="utf-8"
    )
    (release / "RELEASE_MANIFEST.json").write_text(
        json.dumps(
            {
                "document_type": "aset-network-alpha4-release-materialization",
                "assembled_formal": {"scope": "NETWORK_CORE_ADMISSION"},
                "seed_base": {"tree_digest": "placeholder"},
                "extension_bindings": {
                    "relational": "ObserveUnknown -> AdmitFresh,AdmitReplay",
                    "rejected_branch": "REJECT-CONFLICT -> NO_SEED_TRANSITION",
                },
            }
        ),
        encoding="utf-8",
    )
    seed_tree = tree_digest(seed)
    release_manifest = json.loads((release / "RELEASE_MANIFEST.json").read_text())
    release_manifest["seed_base"]["tree_digest"] = seed_tree
    (release / "RELEASE_MANIFEST.json").write_text(json.dumps(release_manifest), encoding="utf-8")
    component_sha = "sha256:" + hashlib.sha256(component.read_bytes()).hexdigest()
    fake_binding = SeedBinding(
        release_tag="seed-test",
        release_tree=seed_tree,
        release_archive="sha256:" + "0" * 64,
        profile_tree="sha256:" + "0" * 64,
        profile_archive="sha256:" + "0" * 64,
        sources={"seed/alpha4/formal/ComponentRelations.tla": component_sha},
        assurance_bases={},
        companions={},
    )
    monkeypatch.setattr(release_tlaps, "parse_seed_binding", lambda: fake_binding)
    verifier = release_tlaps.verifier_source()
    assert "EXTENDS AssembledNetwork, TLAPS" in verifier
    assert "Authorities <- Targets" in verifier
    assert "Seed!ObserveUnknown(s, t, observation.evidence_digest)" in verifier
    assert "Seed!StateType" in verifier
    assert "Next(ns, nt, observation, result)" in verifier
    assert "t.subject = s.subject" in verifier
    assert "t.authority = s.authority" in verifier
    assert r"t.evidence = s.evidence \cup {observation.evidence_digest}" in verifier
    assert "RejectedAdmissionClaimsNoSeedTransition" in verifier
    assert f"THEOREM {release_tlaps.FINAL_THEOREM} ==" in verifier

    fake_tlapm = tmp_path / "tlapm"
    fake_tlapm.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "Path('.tlacache').mkdir(exist_ok=True)\n"
        "print('[INFO]: All 3 obligations proved.')\n",
        encoding="utf-8",
    )
    fake_tlapm.chmod(0o755)
    before = tree_digest(release)
    evidence = release_tlaps.check_release_tlaps(release, seed, str(fake_tlapm))
    assert evidence["status"] == "PASS"
    assert evidence["proof"]["final_theorem"] == release_tlaps.FINAL_THEOREM
    assert evidence["proof"]["obligations_proved"] == 3
    assert evidence["seed_binding"]["operator"] == "ObserveUnknown"
    assert evidence["seed_binding"]["evidence_relation"] == "observation.evidence_digest"
    assert evidence["seed_binding"]["authority_owner"] == "TARGET_LOCAL_SEED"
    assert tree_digest(release) == before
    assert not (release / ".tlacache").exists()
    assert not (seed / ".tlacache").exists()
