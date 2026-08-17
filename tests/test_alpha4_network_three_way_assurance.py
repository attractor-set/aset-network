from __future__ import annotations

from pathlib import Path

import pytest

from tools.alpha4_network_causal_expression import (
    CausalExpressionError,
    load_causal_nets,
    parse_causal_net,
    validate_causal_contract,
)
from tools.alpha4_network_paired_expression import parse_operational_words
from tools.alpha4_network_profile_paired_expression import (
    EXPECTED_DYNAMIC_STACK_EFFECTS,
    EXPECTED_DYNAMIC_WORDS,
    require_words,
)
from tools.alpha4_network_triangulated_expression import check_triangulated_assurance


def test_every_active_network_subject_has_causal_representation() -> None:
    nets = load_causal_nets()
    assert set(nets) == {
        "network",
        "dynamic",
        "federation",
        "liveness",
        "federation-liveness",
    }
    assert {key: len(net.transitions) for key, net in nets.items()} == {
        "network": 3,
        "dynamic": 2,
        "federation": 6,
        "liveness": 4,
        "federation-liveness": 6,
    }
    assert all(net.semantic_precedence == "NONE" for net in nets.values())


def test_network_core_and_all_profiles_are_bounded_three_way_congruent() -> None:
    evidence = check_triangulated_assurance()
    assert evidence["representations"] == ("OPERATIONAL", "RELATIONAL", "CAUSAL")
    assert evidence["semantic_precedence"] == "NONE"
    assert evidence["semantic_delta"] == "NONE"
    assert evidence["pairwise_relations"] == {
        "operational_relational": "PASS",
        "operational_causal": "PASS",
        "relational_causal": "PASS",
    }
    assert evidence["core_cases"] == 272
    assert evidence["dynamic_cases"] == 10
    assert evidence["federation_states"] == 20
    assert evidence["federation_edges"] == 25
    assert evidence["liveness_cases"] == 51
    assert evidence["composition_cases"] == 88
    assert evidence["total_cases"] == 446
    assert evidence["operational_stack_contracts"] == 21
    assert evidence["causal_closed_world_contracts"] == 21
    assert evidence["federation_result_code_bindings"] == 6
    assert evidence["status"] == "PASS"


def test_causal_sources_do_not_replace_relational_temporal_assurance() -> None:
    nets = load_causal_nets()
    assert nets["liveness"].mode == "PREDICATE"
    assert nets["federation-liveness"].mode == "PREDICATE"


def _mutated_source(tmp_path: Path, source: Path, old: str, new: str) -> Path:
    target = tmp_path / source.name
    text = source.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return target


def test_core_operational_stack_contract_rejects_missing_observation(tmp_path: Path) -> None:
    source = Path("network/alpha4/operational/components.forth")
    mutated = _mutated_source(
        tmp_path,
        source,
        "( imports observation -- imports result )",
        "( imports -- imports result )",
    )
    with pytest.raises(RuntimeError, match="stack contract mismatch"):
        parse_operational_words(mutated)


def test_profile_operational_stack_contract_rejects_missing_seed_binding(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/dynamic/operational/components.forth")
    mutated = _mutated_source(
        tmp_path,
        source,
        "( binding seed-binding recognition -- flag )",
        "( binding recognition -- flag )",
    )
    with pytest.raises(RuntimeError, match="stack contract mismatch"):
        require_words(mutated, EXPECTED_DYNAMIC_WORDS, EXPECTED_DYNAMIC_STACK_EFFECTS)


def test_predicate_causal_output_is_closed_world(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/dynamic/causal/components.petri")
    mutated = _mutated_source(tmp_path, source, "OUTPUT VALUE TRUE", "OUTPUT VALUE FALSE")
    net = parse_causal_net(mutated, "ASET-NETWORK-DYNAMIC-ALPHA4-CAUSAL", "PREDICATE")
    with pytest.raises(CausalExpressionError, match="causal output contract drift"):
        validate_causal_contract("dynamic", net)


def test_causal_effect_surface_rejects_unbound_extra_effect(tmp_path: Path) -> None:
    source = Path("network/alpha4/causal/components.petri")
    mutated = _mutated_source(
        tmp_path,
        source,
        "EFFECT ADD_IMPORT",
        "EFFECT ADD_IMPORT\nEFFECT DESTROY_IMPORTS",
    )
    net = parse_causal_net(mutated, "ASET-NETWORK-ALPHA4-CAUSAL", "STATE-TRANSITION")
    with pytest.raises(CausalExpressionError, match="causal effect contract drift"):
        validate_causal_contract("network", net)


def test_federation_causal_result_code_is_closed_world(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/federation/causal/components.petri")
    mutated = _mutated_source(
        tmp_path, source, "OUTPUT CODE FEDERATION_CREATED", "OUTPUT CODE WRONG_CODE"
    )
    net = parse_causal_net(mutated, "ASET-NETWORK-FEDERATION-ALPHA4-CAUSAL", "STATE-TRANSITION")
    with pytest.raises(CausalExpressionError, match="causal output contract drift"):
        validate_causal_contract("federation", net)


def test_relational_source_derivation_and_sensitivity_are_first_class() -> None:
    evidence = check_triangulated_assurance()
    assert evidence["relational_source_derivations"] == 21
    assert evidence["federation_identity_guard_derivations"] == 12
    assert evidence["interface_validator_cases"] == 12
    assert evidence["core_field_sensitivity"] == 5
    assert evidence["dynamic_binding_sensitivity"] == 6
    assert evidence["composition_identity_sensitivity"] == 16


def test_causal_interface_validator_is_not_imported_from_operational_model() -> None:
    source = Path("tools/alpha4_network_causal_expression.py").read_text(encoding="utf-8")
    assert "from tools.alpha4_network_paired_expression import exact_observation" not in source
    assert "def causal_exact_observation" in source


def _copy_repo(tmp_path: Path) -> Path:
    import shutil

    source = Path.cwd()
    target = tmp_path / "repo"
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".tlacache", "dist"),
    )
    subprocess = __import__("subprocess")
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    return target


def _run_gate(repo: Path) -> tuple[int, str]:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "tools.alpha4_network_gate"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def test_bound_federation_tla_guard_mutation_breaks_gate(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    path = repo / "network/alpha4/profiles/federation/formal/FederationRelations.tla"
    text = path.read_text(encoding="utf-8")
    old = 'fs.members[context] = "ABSENT"'
    assert old in text
    path.write_text(text.replace(old, 'fs.members[context] = "ACTIVE"', 1), encoding="utf-8")
    status, output = _run_gate(repo)
    assert status != 0
    assert "relational canonical scope drift" in output.lower()


def test_manifest_duplicate_precedence_breaks_gate(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    path = repo / "network/alpha4/NETWORK.aset"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "SEMANTIC-PRECEDENCE NONE",
            "SEMANTIC-PRECEDENCE OPERATIONAL\nSEMANTIC-PRECEDENCE NONE",
            1,
        ),
        encoding="utf-8",
    )
    status, output = _run_gate(repo)
    assert status != 0
    assert "closed-world declaration drift" in output


def test_manifest_pair_and_proof_scope_are_canonical(tmp_path: Path) -> None:
    from tools.alpha4_network_manifest import ManifestError, parse_network_manifests

    repo = _copy_repo(tmp_path)
    manifest = repo / "network/alpha4/NETWORK.aset"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace(
        "AdmitFresh OperationalAdmitFresh AdmitFreshPairing",
        "BogusRelation OperationalAdmitFresh BogusPairing",
        1,
    )
    manifest.write_text(text, encoding="utf-8")
    with pytest.raises(ManifestError, match="PAIR binding drift"):
        parse_network_manifests(repo)

    repo2 = tmp_path / "repo-proof"
    import shutil

    shutil.copytree(repo, repo2)
    manifest2 = repo2 / "network/alpha4/NETWORK.aset"
    text2 = manifest2.read_text(encoding="utf-8").replace(
        "BogusRelation OperationalAdmitFresh BogusPairing",
        "AdmitFresh OperationalAdmitFresh AdmitFreshPairing",
        1,
    )
    text2 = text2.replace(
        "OperationalRelationalPairing 7",
        "OperationalRelationalPairing 1",
        1,
    )
    manifest2.write_text(text2, encoding="utf-8")
    with pytest.raises(ManifestError, match="proof binding/scope drift"):
        parse_network_manifests(repo2)


def test_federation_artifact_identity_guard_mutation_breaks_gate(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    path = repo / "network/alpha4/profiles/federation/formal/FederationRelations.tla"
    text = path.read_text(encoding="utf-8")
    old = "/\\ artifact \\in Artifacts"
    assert old in text
    path.write_text(text.replace(old, "/\\ TRUE", 1), encoding="utf-8")
    status, output = _run_gate(repo)
    assert status != 0
    assert "relational canonical scope drift" in output.lower()


def test_network_tlaps_runner_rejects_reduced_proof_scope(tmp_path: Path) -> None:
    import subprocess
    import sys

    fake = tmp_path / "tlapm"
    fake.write_text("#!/bin/sh\necho 'All 1 obligation proved.'\n", encoding="utf-8")
    fake.chmod(0o755)
    result = subprocess.run(
        [sys.executable, "tools/run_alpha4_network_tlaps.py", "--tlapm", str(fake)],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode != 0
    assert "SCOPE_DRIFT" in result.stdout


def test_network_profile_tlaps_runner_rejects_reduced_proof_scope(tmp_path: Path) -> None:
    import subprocess
    import sys

    fake = tmp_path / "tlapm"
    fake.write_text("#!/bin/sh\necho 'All 1 obligation proved.'\n", encoding="utf-8")
    fake.chmod(0o755)
    result = subprocess.run(
        [sys.executable, "tools/run_alpha4_network_profile_tlaps.py", "--tlapm", str(fake)],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode != 0
    assert "SCOPE_DRIFT" in result.stdout


def test_relational_and_proof_tla_scopes_are_closed_world(tmp_path: Path) -> None:
    from tools.alpha4_network_manifest import ManifestError, parse_network_manifests

    repo = _copy_repo(tmp_path / "relational")
    relational = repo / "network/alpha4/formal/NetworkRelations.tla"
    text = relational.read_text(encoding="utf-8")
    marker = "/\\ o \\in ObservationUniverse"
    assert marker in text
    relational.write_text(text.replace(marker, marker + "\n    /\\ FALSE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="relational canonical scope drift"):
        parse_network_manifests(repo)

    repo = _copy_repo(tmp_path / "proof")
    proof = repo / "network/alpha4/formal/OperationalRelationalPairingProofs.tla"
    text = proof.read_text(encoding="utf-8")
    theorem = "THEOREM AdmitFreshPairing =="
    assert theorem in text
    proof.write_text(text.replace(theorem, theorem + "\n  /\\ TRUE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="proof canonical scope drift"):
        parse_network_manifests(repo)


def test_network_airgap_rejects_repository_semantic_import() -> None:
    from tools.alpha4_network_expression_airgap import (
        NetworkExpressionAirgapError,
        _validate_companion_ast,
    )

    source = "from tools.alpha4_network_relational_expression import derive_core_contract\n"
    with pytest.raises(NetworkExpressionAirgapError, match="import forbidden"):
        _validate_companion_ast(
            source,
            allowed_imports=frozenset({"hashlib", "pathlib", "typing"}),
            allow_seed_loader=True,
        )


def test_network_airgap_rejects_import_smuggling_and_object_traversal() -> None:
    from tools.alpha4_network_expression_airgap import (
        NetworkExpressionAirgapError,
        _validate_companion_ast,
    )

    with pytest.raises(NetworkExpressionAirgapError, match="import forbidden"):
        _validate_companion_ast(
            "from pathlib import os\n",
            allowed_imports=frozenset({"hashlib", "pathlib", "typing"}),
            allow_seed_loader=True,
        )

    with pytest.raises(NetworkExpressionAirgapError, match="private attribute forbidden"):
        _validate_companion_ast(
            "value = ().__class__\n",
            allowed_imports=frozenset({"hashlib", "pathlib", "typing"}),
            allow_seed_loader=True,
        )


def test_network_release_sensitivity_rejects_known_bug_classes() -> None:
    from tools.alpha4_network_expression_airgap import (
        NetworkExpressionAirgapError,
        _check_composition_identity_sensitivity,
        _check_core_identity_sensitivity,
    )

    def state(subject: str, authority: str) -> dict[str, object]:
        return {
            "subject": subject,
            "authority": authority,
            "recognition": "UNKNOWN",
            "evidence": (),
        }

    def first_only_admit(imports, observation, seed_state):
        same_id = [item for item in imports[:1] if item["import_id"] == observation["import_id"]]
        if observation in same_id:
            code = "IDEMPOTENT_REPLAY"
            next_imports = list(imports)
        elif same_id:
            code = "IDENTIFIER_CONFLICT"
            next_imports = list(imports)
        else:
            code = "IMPORT_ADMITTED"
            next_imports = [*imports, dict(observation)]
        return (
            next_imports,
            dict(seed_state),
            {
                "accepted": code != "IDENTIFIER_CONFLICT",
                "code": code,
                "state_changed": code == "IMPORT_ADMITTED",
            },
        )

    with pytest.raises(NetworkExpressionAirgapError, match="second-position replay"):
        _check_core_identity_sensitivity({"admit_import": first_only_admit}, {"state": state})

    buggy = {
        "delivery_witness": (lambda exported, delivered, export: bool(exported) and bool(delivered))
    }
    with pytest.raises(NetworkExpressionAirgapError, match="foreign-export identity"):
        _check_composition_identity_sensitivity(buggy)


def test_network_formal_reflection_scope_is_closed_world(tmp_path: Path) -> None:
    from tools.alpha4_network_manifest import ManifestError, parse_network_manifests

    repo = _copy_repo(tmp_path)
    reflection = repo / "network/alpha4/formal/RestrictedOperationalSemantics.tla"
    text = reflection.read_text(encoding="utf-8")
    marker = "OperationalAdmitFresh(s, t, o, result) =="
    assert marker in text
    reflection.write_text(text.replace(marker, marker + "\n  /\\ TRUE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="formal reflection canonical scope drift"):
        parse_network_manifests(repo)


def test_network_tla_scope_preserves_comment_tokens_inside_strings(tmp_path: Path) -> None:
    from tools.alpha4_network_manifest import ManifestError, parse_network_manifests

    repo = _copy_repo(tmp_path)
    relational = repo / "network/alpha4/formal/NetworkRelations.tla"
    text = relational.read_text(encoding="utf-8")
    marker = 'result = "IMPORT_ADMITTED"'
    assert marker in text
    relational.write_text(
        text.replace(marker, 'result = "IMPORT_ADMITTED(*scope-drift*)"', 1),
        encoding="utf-8",
    )
    with pytest.raises(ManifestError, match="relational canonical scope drift"):
        parse_network_manifests(repo)
