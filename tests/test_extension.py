from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from reference.network_reference import execute_case

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_upstream_binding_is_exact() -> None:
    binding = json.loads((ROOT / "upstream/ASET_SEED_BINDING.json").read_text(encoding="utf-8"))
    assert binding["canon_id"] == "ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1"
    assert binding["canon_version"] == "0.3.0-alpha.1"
    assert binding["seed_release_tag"] == "seed-0.3.0-alpha.3"
    assert binding["seed_release_commit"] == "633c130187b2a2bb42f24cfd66662d475de385d2"
    assert (
        binding["compatibility_standard"]
        == "ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3"
    )
    assert binding["compatibility_standard_profile"] == "ASET-SEED-COMPATIBILITY-STANDARD-V1"
    assert binding["compatibility"] == "STRICT_EXTENSION_NO_WEAKENING"
    assert binding["implementation_precedence"] == "NONE"


def test_model_preserves_seed_boundary() -> None:
    model = json.loads(
        (ROOT / "extension/canonical/source/network-extension-model.json").read_text(
            encoding="utf-8"
        )
    )
    texts = " ".join(item["text"] for item in model["invariants"])
    assert "target-local Seed" in texts
    assert "may not weaken" in texts
    assert "superior Context" in texts
    assert model["canonicality"]["formal_relation"] == "MACHINE_CHECKABLE_ASSURANCE_BINDING"
    assert model["formal_assurance"]["seed_refinement_proof_evidence"] == (
        "extension/canonical/assurance/seed-refinement-proof.json"
    )
    assert model["formal_assurance"]["seed_refinement_proof_runner"] == (
        "tools/run_seed_refinement_tlaps.py"
    )


def test_all_conformance_cases_match_reference_observables() -> None:
    for path in sorted((ROOT / "extension/canonical/conformance/cases").rglob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        _, actual = execute_case(case)
        assert actual == case["expected"], case["case_id"]


def test_canon_package_integrity() -> None:
    package = json.loads(
        (ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8")
    )
    declared = package.pop("package_digest")
    canonical = (json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    assert declared == "sha256:" + hashlib.sha256(canonical).hexdigest()
    package["package_digest"] = declared
    assert package["canon_id"] == "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA2"
    assert any(item["path"] == "upstream/ASET_SEED_BINDING.json" for item in package["files"])
    for item in package["files"]:
        path = ROOT / item["path"]
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"], item["path"]


def test_import_is_never_accepted_by_observation_alone() -> None:
    case = json.loads(
        (
            ROOT
            / "extension/canonical/conformance/cases/positive/NET-POS-005.json"
        ).read_text(encoding="utf-8")
    )
    state, actual = execute_case(case)
    assert actual["semantic_status"] == "UNKNOWN"
    assert actual["enforcement"] == "BLOCKED"
    assert state is not None and not state["recognitions"]


def test_formal_relation_covers_all_network_invariants() -> None:
    model = json.loads(
        (ROOT / "extension/canonical/source/network-extension-model.json").read_text(
            encoding="utf-8"
        )
    )
    relation = json.loads(
        (ROOT / "extension/canonical/formal/canon-tla-relation.json").read_text(encoding="utf-8")
    )
    assert {item["id"] for item in model["invariants"]} == {
        item["id"] for item in relation["invariant_coverage"]
    }
    assert relation["normative_precedence"] == "MACHINE_READABLE_CANON"
    assert (
        relation["seed_projection"]["exact_seed_tlaps_refinement"]
        == "MECHANICALLY_PROVED"
    )


def test_liveness_is_conditional_and_does_not_require_accept() -> None:
    profile = json.loads(
        (ROOT / "extension/canonical/liveness/liveness-profile.json").read_text(encoding="utf-8")
    )
    assert profile["profile_id"] == "ASET-NETWORK-LIVENESS-V1"
    assert profile["normative"] is True
    assert {item["name"] for item in profile["guarantees"]} == {
        "EVENTUALLY_DELIVERED",
        "EVENTUALLY_OBSERVED",
        "EVENTUALLY_LOCALLY_RESOLVED",
    }
    assert "never requires ACCEPT" in profile["scope_rule"]


def test_tlc_runner_replaces_python_cartesian_model() -> None:
    wrapper = (ROOT / "tools/model_check_network.py").read_text(encoding="utf-8")
    runner = (ROOT / "tools/run_tlc.py").read_text(encoding="utf-8")
    assert "from run_tlc import main" in wrapper
    assert "tlc2.TLC" in runner
    assert "NetworkHistory.cfg" in runner
    assert "NetworkExtensionLiveness.cfg" in runner


def test_tlc_deadlock_policy_distinguishes_quiescence_from_stuck_work() -> None:
    formal = ROOT / "extension/canonical/formal"
    safety_cfg = (formal / "NetworkExtension.cfg").read_text(encoding="utf-8")
    liveness_cfg = (formal / "NetworkExtensionLiveness.cfg").read_text(encoding="utf-8")
    model = (formal / "NetworkExtension.tla").read_text(encoding="utf-8")

    assert "CHECK_DEADLOCK FALSE" in safety_cfg
    assert "CHECK_DEADLOCK FALSE" in liveness_cfg
    assert "NoUnexpectedSafetyDeadlock" in safety_cfg
    assert "NoPendingProgressDeadlock" in liveness_cfg
    assert "SafetyTerminal ==" in model
    assert "ENABLED NetworkAction" in model
    assert "PendingProgress ==" in model
    assert "ENABLED ProgressAction" in model


def test_main_tlc_state_excludes_execution_history() -> None:
    formal = ROOT / "extension/canonical/formal"
    model = (formal / "NetworkExtension.tla").read_text(encoding="utf-8")

    vars_block = model.split("vars ==", 1)[1].split("Init ==", 1)[0]
    assert "history" not in vars_block
    assert "Append(history" not in model
    assert "NetworkHistory" in model


def test_history_trace_is_separate_bounded_tlc_model() -> None:
    formal = ROOT / "extension/canonical/formal"
    model = (formal / "NetworkHistory.tla").read_text(encoding="utf-8")
    config = (formal / "NetworkHistory.cfg").read_text(encoding="utf-8")
    relation = json.loads((formal / "canon-tla-relation.json").read_text(encoding="utf-8"))

    assert "HistoryPrefixPreserved" in model
    assert "AcceptedTransitionAppendsExactlyOne" in model
    assert "HistoryDigests = {D1, D2, D3, D4}" in config
    assert relation["history_model"]["scope"] == "NET-INV-010_TRACE_PROJECTION"
    coverage = {item["id"]: item for item in relation["invariant_coverage"]}
    assert coverage["NET-INV-010"]["status"] == "TLC_TRACE_PROPERTY"


def test_canon_package_excludes_tlc_runtime_metadata() -> None:
    builder = (ROOT / "tools/build_canon_package.py").read_text(encoding="utf-8")
    assert 'CANON_SUFFIXES = {".json", ".tla", ".cfg"}' in builder
    assert 'relative.parts[0] == "formal" and len(relative.parts) != 2' in builder
    assert "included_in_canon(path)" in builder


def test_tlc_runtime_metadata_is_outside_normative_canon() -> None:
    runner = (ROOT / "tools/run_tlc.py").read_text(encoding="utf-8")
    assert 'TLC_METADATA_ROOT = ROOT / ".tooling/tlc"' in runner
    assert '"-metadir"' in runner
    assert "shutil.rmtree(metadir)" in runner


def test_canon_separates_semantic_state_from_evidence_history() -> None:
    model = json.loads(
        (ROOT / "extension/canonical/source/network-extension-model.json").read_text(
            encoding="utf-8"
        )
    )
    partition = model["state_partition"]
    semantic = set(partition["semantic_state_fields"])
    evidence = set(partition["evidence_history_fields"])
    assert semantic | evidence == set(model["state"])
    assert not semantic & evidence
    assert evidence == {"history"}
    assert partition["evidence_history_role"] == "NORMATIVE_APPEND_ONLY_EVIDENCE_TRACE"
    assert "MUST NOT itself confer Authority" in partition["transition_enabling_rule"]
    inv10 = next(item for item in model["invariants"] if item["id"] == "NET-INV-010")
    assert "canonical evidence history" in inv10["text"]
    assert "does not itself confer Authority" in inv10["text"]


def test_liveness_is_optional_normative_claim_not_core_requirement() -> None:
    live = json.loads(
        (ROOT / "extension/canonical/liveness/liveness-profile.json").read_text(
            encoding="utf-8"
        )
    )
    core = json.loads(
        (ROOT / "extension/canonical/conformance/conformance-profile.json").read_text(
            encoding="utf-8"
        )
    )
    claim = live["claim_semantics"]
    assert claim["claim_type"] == "OPTIONAL_CAPABILITY_CLAIM"
    assert claim["required_for_core_conformance"] is False
    assert claim["assumptions_must_be_declared"] is True
    assert live["resolution_semantics"]["terminal_local_results"] == ["ACCEPT", "DENY"]
    assert live["resolution_semantics"]["eventual_accept_required"] is False
    optional = {item["profile_id"]: item for item in core["optional_claim_profiles"]}
    assert optional["ASET-NETWORK-LIVENESS-V1"]["required_for_core_conformance"] is False
    assert optional["ASET-NETWORK-LIVENESS-V1"]["normative_when_claimed"] is True


def test_formal_relation_exposes_three_canon_projection_surfaces() -> None:
    relation = json.loads(
        (ROOT / "extension/canonical/formal/canon-tla-relation.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = relation["projection_surfaces"]
    assert surfaces["semantic_state"]["formal_model"] == "NetworkExtension"
    assert (
        surfaces["semantic_state"]["canon_selector"]
        == "/state_partition/semantic_state_fields"
    )
    assert surfaces["evidence_history"]["formal_model"] == "NetworkHistory"
    assert (
        surfaces["evidence_history"]["canon_selector"]
        == "/state_partition/evidence_history_fields"
    )
    assert surfaces["conditional_liveness"]["scope"] == "ASET-NETWORK-LIVENESS-V1"
    assert relation["liveness_model"]["required_for_core_conformance"] is False


def test_seed_refinement_bridge_is_mechanically_proved_without_vendoring_seed() -> None:
    formal = ROOT / "extension/canonical/formal"
    relation = json.loads((formal / "canon-tla-relation.json").read_text(encoding="utf-8"))
    refinement = relation["seed_refinement"]

    assert refinement["mapping_module"] == "NetworkExtensionSeedRefinement"
    assert refinement["proof_module"] == "NetworkExtensionSeedRefinementProofs"
    assert refinement["upstream_module"] == "SeedResolution"
    assert refinement["upstream_materialization"] == "EXTERNAL_PINNED_SEED_SOURCE_NOT_VENDORED"
    assert refinement["status"] == "MECHANICALLY_PROVED"
    assert relation["seed_projection"]["exact_seed_tlaps_refinement"] == "MECHANICALLY_PROVED"
    assert refinement["obligations_proved"] == 261
    assert refinement["obligation_count_semantics"] == (
        "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT"
    )
    assert refinement["upstream_sha256"] == (
        "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
    )
    assert not (formal / "SeedResolution.tla").exists()


def test_seed_refinement_proof_evidence_binds_exact_artifacts() -> None:
    formal = ROOT / "extension/canonical/formal"
    evidence_path = ROOT / "extension/canonical/assurance/seed-refinement-proof.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert evidence["status"] == "MECHANICALLY_PROVED"
    assert evidence["scope"] == "PINNED_SEED_REFINEMENT"
    assert evidence["proof_gate"]["verdict"] == "PASS"
    assert evidence["proof_gate"]["obligations_proved"] == 261
    assert evidence["proof_gate"]["obligation_count_semantics"] == (
        "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT"
    )
    assert evidence["tlapm"]["commit"] == (
        "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
    )
    assert evidence["upstream_seed"]["release_commit"] == (
        "633c130187b2a2bb42f24cfd66662d475de385d2"
    )
    assert evidence["upstream_seed"]["sha256"] == (
        "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
    )
    for key, filename in (
        ("mapping", "NetworkExtensionSeedRefinement.tla"),
        ("proof", "NetworkExtensionSeedRefinementProofs.tla"),
    ):
        artifact = evidence["network_artifacts"][key]
        assert artifact["path"] == f"extension/canonical/formal/{filename}"
        assert artifact["sha256"] == sha(formal / filename)


def test_seed_refinement_limit_records_proved_abstraction_boundary() -> None:
    limitations = json.loads(
        (ROOT / "extension/canonical/assurance/limitations.json").read_text(encoding="utf-8")
    )
    item = next(entry for entry in limitations["limitations"] if entry["id"] == "NET-LIMIT-005")
    assert item["status"] == "PINNED_ABSTRACTION_REFINEMENT_PROVED"
    assert "mechanically proved by TLAPS" in item["description"]


def test_seed_refinement_mapping_has_exact_network_to_seed_action_roles() -> None:
    model = (
        ROOT / "extension/canonical/formal/NetworkExtensionSeedRefinement.tla"
    ).read_text(encoding="utf-8")

    assert "Seed == INSTANCE SeedResolution" in model
    assert "ResolutionIds <- ExportUniverse" in model
    assert "Bindings <- BridgeBindings" in model
    assert "BridgeBinding(e) == <<e.target, e.artifact>>" in model
    assert "Authorities <- Contexts" in model
    assert "BridgeObserveAsSeedRegister" in model
    assert "BridgeAcceptAsSeedSubmit" in model
    assert "BridgeDenyAsSeedSubmit" in model
    assert 'Seed!SubmitResolution(e, BridgeBinding(e), e.target, "ALLOW")' in model
    assert 'Seed!SubmitResolution(e, BridgeBinding(e), e.target, "BLOCK")' in model
    assert "NetworkOnlyAction" in model


def test_seed_refinement_proof_declares_behavioral_and_evaluator_theorems() -> None:
    proof = (
        ROOT / "extension/canonical/formal/NetworkExtensionSeedRefinementProofs.tla"
    ).read_text(encoding="utf-8")

    assert "THEOREM NetworkSafetyRefinesSeedResolution ==" in proof
    assert "THEOREM NetworkEvaluatorMatchesSeedResolution ==" in proof
    assert "ObserveRefinesSeedRegisterRequest" in proof
    assert "ResolveAcceptRefinesSeedSubmitAllow" in proof
    assert "ResolveDenyRefinesSeedSubmitBlock" in proof
    assert "NetworkOnlyActionsStutterAtSeedBoundary" in proof


def test_seed_refinement_tlaps_runner_pins_upstream_and_tlapm() -> None:
    runner = (ROOT / "tools/run_seed_refinement_tlaps.py").read_text(encoding="utf-8")
    assert 'EXPECTED_TLAPM_VERSION = "4600b24"' in runner
    assert 'EXPECTED_SEED_RELEASE_COMMIT = "633c130187b2a2bb42f24cfd66662d475de385d2"' in runner
    assert "1c0ebb27ed52da289f0981dcb11b61b6" in runner
    assert '"-I",' in runner
    assert "NETWORK_SEED_TLAPS_VERDICT" in runner
    assert "seed-refinement-proof.json" in runner
    assert "recorded_obligations" in runner


def test_formal_release_gate_requires_all_formal_stages() -> None:
    gate = (ROOT / "tools/run_formal_release_gate.py").read_text(encoding="utf-8")
    for marker in (
        "DIFF_CHECK",
        "BUILD_CANON_PACKAGE",
        "VALIDATE",
        "CONFORMANCE",
        "TESTS",
        "TLC",
        "TLAPS_SEED_REFINEMENT",
        "FORMAL_RELEASE_GATE=PASS",
    ):
        assert marker in gate



def test_network_canon_projection_is_standalone_generated_from_exact_model() -> None:
    formal = ROOT / "extension/canonical/formal"
    model = ROOT / "extension/canonical/source/network-extension-model.json"
    projection = (formal / "NetworkCanonProjection.tla").read_text(encoding="utf-8")
    assert "GENERATED FILE. DO NOT EDIT." in projection
    assert "ASET-NETWORK-CANON-TLA-PROJECTION-V2" in projection
    assert sha(model) in projection
    assert "EXTENDS NetworkExtension" not in projection
    assert "INSTANCE NetworkExtension" not in projection
    assert "CanonSafetySpec == CanonInit /\\ [][CanonNetworkAction]_CanonVars" in projection


def test_network_canon_projection_generator_exact_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, "tools/generate_canon_tla_projection.py", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "NETWORK_CANON_PROJECTION_CHECK=PASS" in result.stdout


def test_network_canon_refinement_relation_binds_exact_source_and_target() -> None:
    relation_path = ROOT / "extension/canonical/assurance/canon-tla-refinement.json"
    relation = json.loads(relation_path.read_text(encoding="utf-8"))
    assert relation["relation_type"] == (
        "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF"
    )
    assert relation["generated_projection"]["profile"] == (
        "ASET-NETWORK-CANON-TLA-PROJECTION-V2"
    )
    assert relation["source_model"]["sha256"] == sha(
        ROOT / relation["source_model"]["path"]
    )
    assert relation["target_model"]["sha256"] == sha(
        ROOT / relation["target_model"]["path"]
    )
    assert relation["proof"]["final_theorem"] == (
        "NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection"
    )
    assert relation["status"] == "MECHANICALLY_PROVED"
    assert relation["proof_evidence"]["status"] == "MECHANICALLY_PROVED"
    assert relation["proof_evidence"]["obligations_proved"] == 3


def test_network_canon_refinement_proof_evidence_is_exact() -> None:
    evidence = json.loads(
        (
            ROOT / "extension/canonical/assurance/canon-refinement-proof.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["status"] == "MECHANICALLY_PROVED"
    assert evidence["projection_profile"] == "ASET-NETWORK-CANON-TLA-PROJECTION-V2"
    assert evidence["proof_gate"]["verdict"] == "PASS"
    assert evidence["proof_gate"]["obligations_proved"] == 3
    assert evidence["proof_gate"]["obligation_count_semantics"] == (
        "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT"
    )
    assert evidence["tlapm"]["commit"] == (
        "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
    )
    for artifact in evidence["network_artifacts"].values():
        assert artifact["sha256"] == sha(ROOT / artifact["path"])


def test_network_canon_refinement_proof_is_seed_style_explicit_instance() -> None:
    proof = (
        ROOT / "extension/canonical/formal/NetworkCanonRefinementProofs.tla"
    ).read_text(encoding="utf-8")
    assert "EXTENDS NetworkExtension, TLAPS" in proof
    assert "Canon == INSTANCE NetworkCanonProjection" in proof
    assert "THEOREM NetworkCanonCoreAlgebraEquivalent ==" in proof
    assert "THEOREM NetworkCoreSafetyPredicatesEquivalentToCanonProjection ==" in proof
    assert "THEOREM NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection ==" in proof


def test_formal_release_gate_requires_canon_projection_and_canon_tlaps() -> None:
    gate = (ROOT / "tools/run_formal_release_gate.py").read_text(encoding="utf-8")
    assert "CANON_PROJECTION_CHECK" in gate
    assert "TLAPS_CANON_REFINEMENT" in gate
    assert "run_canon_refinement_tlaps.py" in gate
    assert "FORMAL_RELEASE_CANON_REFINEMENT_OBLIGATIONS" in gate
    assert "FORMAL_RELEASE_CANON_REFINEMENT_STATUS" in gate


def test_inpi_deposit_snapshot_matches_seed_deterministic_pattern() -> None:
    builder = ROOT / "tools/build_release.py"
    archive = ROOT / "dist/ASET-Network-Extension-Repository-Snapshot.zip"
    checksum = archive.with_suffix(archive.suffix + ".sha256")

    first = subprocess.run(
        [sys.executable, str(builder)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert first.returncode == 0, first.stdout
    first_digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    second = subprocess.run(
        [sys.executable, str(builder)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert second.returncode == 0, second.stdout
    second_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert second_digest == first_digest

    declared_digest, declared_name = checksum.read_text(encoding="utf-8").strip().split()
    assert declared_digest == second_digest
    assert declared_name == archive.name

    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert names
        assert all(name.startswith("ASET-Network-Extension/") for name in names)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in bundle.infolist())
        banned = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            ".tlacache",
            ".tooling",
            "states",
            "dist",
            "build",
        }
        assert all(not (set(Path(name).parts) & banned) for name in names)


def test_ci_runs_full_formal_gate_with_pinned_seed_and_tlapm() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "tlapm-1.6.0-pre-x86_64-linux-gnu.tar.gz" in workflow
    assert "bfa5e5350ac1ec7202feecad0a4a71a5bb58c16a49660448b35b6f371ba9e2f5" in workflow
    assert 'test "$("$tlapm_bin" --version)" = "4600b24"' in workflow
    assert "633c130187b2a2bb42f24cfd66662d475de385d2" in workflow
    assert "python tools/run_formal_release_gate.py" in workflow
    assert '--tlapm "$TLAPM_BIN"' in workflow
    assert '--seed-root "$SEED_ROOT"' in workflow
    assert "dist/formal-release-gate.json" in workflow
    assert "dist/network-canon-refinement-proof.json" in workflow
    assert "dist/network-seed-refinement-proof.json" in workflow


def test_ci_publishes_inpi_deposit_sha256_like_seed() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    builder = (ROOT / "tools/build_release.py").read_text(encoding="utf-8")
    assert "python tools/build_release.py" in workflow
    assert "INPI_DEPOSIT_SHA256=%s" in workflow
    assert "REGULATOR_SNAPSHOT_SHA256" not in workflow
    assert 'print(f"INPI_DEPOSIT_SHA256={digest}")' in builder
    assert 'print("INPI_DEPOSIT=PASS")' in builder
    assert "ASET-Network-Extension-Repository-Snapshot.zip.sha256" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "aset-network-extension-inpi-deposit-${{ github.sha }}" in workflow


def test_dynamic_profiles_are_seed_bound_without_network_state_or_transitions() -> None:
    profile = json.loads(
        (ROOT / "extension/canonical/protocol/dynamic-profile-profile.json").read_text(
            encoding="utf-8"
        )
    )
    assert profile["profile_id"] == "ASET-NETWORK-DYNAMIC-PROFILES-V1"
    assert profile["normative"] is True
    assert profile["claim_semantics"] == {
        "claim_type": "OPTIONAL_CAPABILITY_CLAIM",
        "normative_when_claimed": True,
        "required_for_core_conformance": False,
    }
    assert profile["core_boundary"]["network_state_fields_added"] == []
    assert profile["core_boundary"]["network_transition_kinds_added"] == []
    assert profile["core_boundary"]["network_owned_activation_state"] is False
    assert profile["activation_semantics"]["rule"] == (
        "TARGET_LOCAL_SEED_ALLOW_ON_PROJECTED_EXACT_PROFILE_BINDING"
    )
    assert profile["activation_semantics"]["active_profile_registry_is_normative_state"] is False
    assert profile["activation_semantics"]["seed_binding_projection"] == {
        "binding_digest": "Seed canonical ResolutionBinding digest over the projected fields",
        "context_id": "ProfileBinding.target_context_id",
        "policy_epoch": "ProfileBinding.target_policy_epoch",
        "question_digest": "ProfileBinding.profile_digest",
        "scope": "ProfileBinding.seed_scope",
        "state_root": "ProfileBinding.target_state_root",
    }
    assert profile["digest_profile"]["canonicalization"] == (
        "RFC8785_JSON_CANONICALIZATION_SCHEME"
    )
    assert profile["refinement_semantics"]["may_strengthen_parent"] is True
    assert profile["refinement_semantics"]["may_weaken_parent"] is False
    assert profile["refinement_semantics"]["may_supersede_seed"] is False


def test_dynamic_profile_wire_objects_are_exact_and_have_no_activation_field() -> None:
    schema_dir = ROOT / "extension/canonical/protocol/schemas"
    definition = json.loads((schema_dir / "profile-definition.schema.json").read_text())
    binding = json.loads((schema_dir / "profile-binding.schema.json").read_text())

    assert definition["additionalProperties"] is False
    assert set(definition["required"]) == {
        "profile_id",
        "profile_version",
        "parent_contract_digest",
        "scope_digest",
        "requirements_digest",
        "invariants_digest",
        "profile_digest",
    }
    assert "activation" not in definition["properties"]
    assert "status" not in definition["properties"]

    assert binding["additionalProperties"] is False
    assert set(binding["required"]) == {
        "binding_digest",
        "profile_digest",
        "target_context_id",
        "target_state_root",
        "target_policy_epoch",
        "seed_scope",
    }
    assert "active" not in binding["properties"]
    assert "semantic_status" not in binding["properties"]
    assert "enforcement" not in binding["properties"]
    assert "resolution_id" not in binding["properties"]
    assert "question_digest" not in binding["properties"]


def test_dynamic_profile_is_optional_core_claim() -> None:
    core = json.loads(
        (ROOT / "extension/canonical/conformance/conformance-profile.json").read_text(
            encoding="utf-8"
        )
    )
    claims = {item["profile_id"]: item for item in core["optional_claim_profiles"]}
    claim = claims["ASET-NETWORK-DYNAMIC-PROFILES-V1"]
    assert claim["required_for_core_conformance"] is False
    assert claim["normative_when_claimed"] is True
    assert claim["activation_authority"] == "TARGET_LOCAL_SEED_ONLY"
