from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from reference.network_reference import apply_transition, execute_case
from reference.legacy_network_reference import execute_case as execute_legacy_case

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_upstream_binding_is_exact() -> None:
    b=json.loads((ROOT/"upstream/ASET_SEED_BINDING.json").read_text())
    assert b["seed_release_tag"]=="seed-0.3.0-alpha.3"
    assert b["seed_release_commit"]=="633c130187b2a2bb42f24cfd66662d475de385d2"
    assert b["compatibility"]=="STRICT_EXTENSION_NO_WEAKENING"
    assert b["implementation_precedence"]=="NONE"


def test_normative_core_is_one_state_one_transition() -> None:
    m=json.loads((ROOT/"extension/canonical/source/network-extension-model.json").read_text())
    assert m["version"]=="0.1.0-alpha.3"
    assert m["status"]=="MINIMAL_ADMISSION_CORE_ALPHA3_NORMATIVE_CUTOVER"
    assert m["state_partition"]["semantic_state_fields"]==["imports"]
    assert m["state_partition"]["evidence_history_fields"]==["history"]
    assert m["transition_kinds"]==["ADMIT_IMPORT"]
    assert "recognitions" not in m["state"]


def test_core_conformance_cases_match_minimal_reference() -> None:
    p=json.loads((ROOT/"extension/canonical/conformance/conformance-profile.json").read_text())
    assert p["profile_id"]=="ASET-NETWORK-EXTENSION-CONFORMANCE-V2"
    assert p["case_count"]==4
    for item in p["cases"]:
        case=json.loads((ROOT/item["path"]).read_text())
        _,actual=execute_case(case)
        assert actual==case["expected"],case["case_id"]


def test_admission_is_fail_closed() -> None:
    case=json.loads((ROOT/"extension/canonical/conformance/cases/positive/NET-POS-001.json").read_text())
    state,result=execute_case(case)
    assert result["semantic_status"]=="UNKNOWN"
    assert result["enforcement"]=="BLOCKED"
    assert state["imports"]
    assert "recognitions" not in state


def test_admission_exact_replay_is_idempotent() -> None:
    case=json.loads((ROOT/"extension/canonical/conformance/cases/positive/NET-POS-002.json").read_text())
    before=json.loads(json.dumps(case["initial_state"]))
    state,result=execute_case(case)
    assert result["code"]=="IDEMPOTENT_REPLAY"
    assert result["state_changed"] is False
    assert state==before


def test_admission_conflict_is_rejected() -> None:
    case=json.loads((ROOT/"extension/canonical/conformance/cases/negative/NET-NEG-001.json").read_text())
    before=json.loads(json.dumps(case["initial_state"]))
    state,result=execute_case(case)
    assert result["code"]=="IDENTIFIER_CONFLICT"
    assert result["accepted"] is False
    assert state==before


def test_generated_projection_is_current() -> None:
    r=subprocess.run([sys.executable,"tools/generate_canon_tla_projection.py","--check"],cwd=ROOT,text=True,capture_output=True)
    assert r.returncode==0,r.stdout+r.stderr
    assert "NETWORK_CANON_PROJECTION_CHECK=PASS" in r.stdout


def test_formal_core_has_one_variable_and_one_action() -> None:
    t=(ROOT/"extension/canonical/formal/NetworkExtension.tla").read_text()
    assert "VARIABLE imports" in t
    assert "VARIABLES" not in t
    assert "AdmitImport(o) ==" in t
    for legacy in ["Join(c)","GrantRoute", "ResolveAccept", "ResolveDeny", "Withdraw(c)"]:
        assert legacy not in t


def test_alpha3_proof_evidence_is_materialized_and_exact() -> None:
    expected={
        "canon-refinement-proof.json":3,
        "seed-refinement-proof.json":35,
        "legacy-admission-refinement-proof.json":23,
    }
    for name,count in expected.items():
        e=json.loads((ROOT/"extension/canonical/assurance"/name).read_text())
        assert e["status"]=="MECHANICALLY_PROVED"
        assert e["proof_gate"]["verdict"]=="MECHANICALLY_PROVED"
        assert e["proof_gate"]["obligations_proved"]==count
        assert e["proof_gate"]["materialization"]=="REPRODUCED_WITH_PINNED_TLAPM"

    rel=json.loads((ROOT/"extension/canonical/formal/canon-tla-relation.json").read_text())
    assert rel["canon_projection"]["status"]=="MECHANICALLY_PROVED"
    assert rel["canon_projection"]["obligations_proved"]==3
    assert rel["seed_refinement"]["status"]=="MECHANICALLY_PROVED"
    assert rel["seed_refinement"]["obligations_proved"]==35
    assert rel["legacy_alpha2_refinement"]["status"]=="MECHANICALLY_PROVED"
    assert rel["legacy_alpha2_refinement"]["obligations_proved"]==23


def test_legacy_alpha2_traces_project_to_minimal_core() -> None:
    from tools.verify_minimal_core_reduction import verify_conformance_trace_projection
    assert verify_conformance_trace_projection()==18


def test_federation_profile_is_post_cutover_owner() -> None:
    f=json.loads((ROOT/"extension/canonical/protocol/federation-profile.json").read_text())
    e=f["extraction_semantics"]
    assert e["phase"]=="NORMATIVE_PROFILE_AFTER_CORE_CUTOVER"
    assert e["normative_core_changed_by_this_slice"] is True
    assert e["network_admission_state_retained"]==["imports"]
    assert e["seed_derived_legacy_state_fields"]==["recognitions"]
    assert set(e["profile_owned_legacy_transition_kinds"])=={"FEDERATION_GENESIS","MEMBER_JOIN","ROUTE_GRANT","EXPORT_ARTIFACT","SUSPEND_ROUTE","MEMBER_WITHDRAW"}


def test_federation_conformance_is_optional_and_legacy_backed() -> None:
    p=json.loads((ROOT/"extension/canonical/conformance/federation-profile-conformance-profile.json").read_text())
    assert p["required_for_core_conformance"] is False
    assert p["case_count"]==10
    for item in p["cases"]:
        assert "/legacy-alpha2-cases/" in item["path"]
        case=json.loads((ROOT/item["path"]).read_text())
        _,actual=execute_legacy_case(case)
        assert actual==case["expected"]


def test_package_is_alpha3_and_self_consistent() -> None:
    p=json.loads((ROOT/"extension/canonical/CANON_PACKAGE.json").read_text())
    declared=p.pop("package_digest")
    canonical=(json.dumps(p,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
    assert declared=="sha256:"+hashlib.sha256(canonical).hexdigest()
    assert p["extension_version"]=="0.1.0-alpha.3"
    assert p["canon_id"]=="ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3"


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


def test_dynamic_profile_target_context_domain_is_closed_under_seed_projection() -> None:
    schema = json.loads(
        (
            ROOT / "extension/canonical/protocol/schemas/profile-binding.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert schema["properties"]["target_context_id"] == {
        "type": "string",
        "minLength": 3,
        "maxLength": 256,
        "pattern": r"^[A-Za-z0-9][A-Za-z0-9._:/\-]*$",
    }
    assert schema["properties"]["target_policy_epoch"] == {
        "type": "integer",
        "minimum": 0,
        "maximum": 9007199254740991,
    }


def test_dynamic_profile_content_addressing_is_executable() -> None:
    from tools.dynamic_profile_conformance import content_digest, validate_wire_object

    profile = json.loads(
        (
            ROOT
            / "extension/canonical/conformance/dynamic-profile-cases/positive/DP-POS-001.json"
        ).read_text(encoding="utf-8")
    )["object"]
    accepted, code = validate_wire_object("PROFILE_DEFINITION", profile)
    assert (accepted, code) == (True, "PROFILE_DEFINITION_VALID")
    assert profile["profile_digest"] == content_digest(profile, "profile_digest")

    mutated = dict(profile)
    mutated["profile_version"] = "v2"
    accepted, code = validate_wire_object("PROFILE_DEFINITION", mutated)
    assert (accepted, code) == (False, "PROFILE_DIGEST_MISMATCH")


def test_dynamic_profile_binding_digest_is_executable() -> None:
    from tools.dynamic_profile_conformance import content_digest, validate_wire_object

    binding = json.loads(
        (
            ROOT
            / "extension/canonical/conformance/dynamic-profile-cases/positive/DP-POS-002.json"
        ).read_text(encoding="utf-8")
    )["object"]
    accepted, code = validate_wire_object("PROFILE_BINDING", binding)
    assert (accepted, code) == (True, "PROFILE_BINDING_VALID")
    assert binding["binding_digest"] == content_digest(binding, "binding_digest")


def test_dynamic_profile_allow_does_not_carry_across_state_root_change() -> None:
    from tools.dynamic_profile_conformance import execute_case as execute_profile_case

    case = json.loads(
        (
            ROOT
            / "extension/canonical/conformance/dynamic-profile-cases/negative/DP-NEG-004.json"
        ).read_text(encoding="utf-8")
    )
    assert execute_profile_case(case) == case["expected"]
    assert case["expected"] == {"accepted": False, "code": "SEED_BINDING_MISMATCH"}


def test_dynamic_profile_refinement_claim_does_not_imply_proof_status() -> None:
    profile = json.loads(
        (
            ROOT / "extension/canonical/protocol/dynamic-profile-profile.json"
        ).read_text(encoding="utf-8")
    )
    assurance = profile["assurance_semantics"]
    assert assurance["base_refinement_claim"] == (
        "NORMATIVE_NO_WEAKENING_OBLIGATION_NOT_PROOF_STATUS"
    )
    assert assurance["refinement_evidence_digest_optional"] is True
    assert assurance["presence_means"] == "BINDS_AN_EXTERNAL_EVIDENCE_ARTIFACT_ONLY"
    assert "MUST NOT claim MECHANICALLY_PROVED" in assurance["mechanically_proved_status_rule"]


def test_dynamic_profile_optional_conformance_cases_are_exact() -> None:
    from tools.dynamic_profile_conformance import run_profile_conformance

    profile = json.loads(
        (
            ROOT / "extension/canonical/conformance/dynamic-profile-conformance-profile.json"
        ).read_text(encoding="utf-8")
    )
    assert profile["claims_profile"] == "ASET-NETWORK-DYNAMIC-PROFILES-V1"
    assert profile["required_for_core_conformance"] is False
    assert profile["case_count"] == 8
    assert profile["positive_count"] == 3
    assert profile["negative_count"] == 5
    assert run_profile_conformance() == []


def test_dynamic_profile_seed_projection_digest_matches_pinned_seed_canonical_form() -> None:
    from tools.dynamic_profile_conformance import project_seed_binding

    case = json.loads(
        (
            ROOT
            / "extension/canonical/conformance/dynamic-profile-cases/positive/DP-POS-002.json"
        ).read_text(encoding="utf-8")
    )
    projected = project_seed_binding(case["object"])
    payload = {key: value for key, value in projected.items() if key != "binding_digest"}
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
    assert projected["binding_digest"] == expected




def test_federation_profile_definition_is_valid_after_cutover() -> None:
    from tools.dynamic_profile_conformance import validate_wire_object
    p=ROOT/"extension/canonical/protocol/profiles/federation-profile-definition.json"
    d=json.loads(p.read_text())
    assert validate_wire_object("PROFILE_DEFINITION",d)==(True,"PROFILE_DEFINITION_VALID")
    assert d["parent_contract_digest"]==sha(ROOT/"extension/canonical/source/network-extension-model.json")


def test_full_local_non_tlaps_validation_stack() -> None:
    for cmd in [
        [sys.executable,"tools/validate_extension.py"],
        [sys.executable,"tools/verify_minimal_core_reduction.py"],
        [sys.executable,"tools/run_conformance.py"],
    ]:
        r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        assert r.returncode==0,r.stdout+r.stderr


def test_release_metadata_matches_alpha3_minimal_admission() -> None:
    project=tomllib.loads((ROOT/"pyproject.toml").read_text())["project"]
    assert project["version"]=="0.1.0a3"
    assert project["description"]=="Minimal cross-context evidence admission extension for ASET Seed"


def test_liveness_profile_preserves_seed_resolution_ownership() -> None:
    live=json.loads((ROOT/"extension/canonical/liveness/liveness-profile.json").read_text())
    assert live["parent_profile"]=="ASET-NETWORK-FEDERATION-PROFILE-V1"
    assert live["resolution_semantics"]["resolution_owner"]=="PINNED_TARGET_LOCAL_SEED"
    assert live["resolution_semantics"]["terminal_local_results"]==["ALLOW","BLOCK"]
    assert live["resolution_semantics"]["legacy_assurance_projection"]=={"ACCEPT":"ALLOW","DENY":"BLOCK"}
    a3=next(x for x in live["assumptions"] if x["id"]=="NET-LIVE-A-003")
    assert a3["name"]=="TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION"


def test_reduction_metadata_no_longer_calls_normative_core_candidate() -> None:
    reduction=json.loads((ROOT/"extension/canonical/assurance/minimal-core-reduction.json").read_text())
    assert "candidate" not in reduction
    assert reduction["normative_core"]["semantic_state_fields"]==["imports"]
    assert reduction["normative_core"]["transition_kinds"]==["ADMIT_IMPORT"]
    fed=json.loads((ROOT/"extension/canonical/protocol/federation-profile.json").read_text())
    assert "candidate_network_transition" not in fed["extraction_semantics"]
    assert fed["extraction_semantics"]["normative_network_transition"]==["ADMIT_IMPORT"]


def test_tlc_append_only_property_is_temporal_harness_only() -> None:
    formal = ROOT / "extension/canonical/formal"
    normative = (formal / "NetworkExtension.tla").read_text()
    harness = (formal / "NetworkExtensionTLC.tla").read_text()
    base_cfg = (formal / "NetworkExtension.cfg").read_text()
    harness_cfg = (formal / "NetworkExtensionTLC.cfg").read_text()
    runner = (ROOT / "tools/run_tlc.py").read_text()

    assert "ImportsAppendOnly == imports \\subseteq imports'" in normative
    assert "ImportsAppendOnlyTemporal == [][ImportsAppendOnly]_vars" in harness
    assert "PROPERTIES" not in base_cfg
    assert "ImportsAppendOnlyTemporal" in harness_cfg
    assert "'safety':('NetworkExtensionTLC.tla','NetworkExtensionTLC.cfg')" in runner


def test_tlc_harness_does_not_change_normative_proof_target() -> None:
    relation = json.loads(
        (ROOT / "extension/canonical/formal/canon-tla-relation.json").read_text()
    )
    assert relation["target_model"]["module"] == "NetworkExtension"
    assert relation["target_model"]["path"] == "extension/canonical/formal/NetworkExtension.tla"
    assert relation["tlc_harness"]["scope"] == "BOUNDED_TEMPORAL_MODEL_CHECKING_ONLY"
    assert relation["tlc_harness"]["properties"] == ["ImportsAppendOnlyTemporal"]


def test_rights_baseline_captures_alpha3_release_and_full_proof_chain() -> None:
    from tools.build_rights_baseline import ARTIFACTS

    artifacts = set(ARTIFACTS)
    required = {
        "pyproject.toml",
        "extension/canonical/CANON_PACKAGE.json",
        "extension/canonical/source/network-extension-model.json",
        "extension/canonical/formal/canon-tla-relation.json",
        "extension/canonical/formal/NetworkCanonRefinementProofs.tla",
        "extension/canonical/formal/NetworkExtensionSeedRefinement.tla",
        "extension/canonical/formal/NetworkExtensionSeedRefinementProofs.tla",
        "extension/canonical/formal/NetworkLegacyAlpha2.tla",
        "extension/canonical/formal/NetworkLegacyAdmissionRefinement.tla",
        "extension/canonical/formal/NetworkLegacyAdmissionRefinementProofs.tla",
        "extension/canonical/assurance/canon-refinement-proof.json",
        "extension/canonical/assurance/seed-refinement-proof.json",
        "extension/canonical/assurance/legacy-admission-refinement-proof.json",
        "upstream/ASET_SEED_BINDING.json",
    }
    assert required <= artifacts
