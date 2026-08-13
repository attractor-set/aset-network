from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from reference.profiles.federation import execute_case as execute_federation_case
from tools.dynamic_profile_conformance import run_profile_conformance, validate_wire_object

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "extension/canonical"
CORE_SCHEMAS = C / "protocol/schemas"
PROFILE_SCHEMA_DIRS = sorted((C / "profiles").glob("*/schemas"))
UP = ROOT / "upstream/ASET_SEED_BINDING.json"
EXPECTED_SEED = {
    "seed_release_tag": "seed-0.3.0-alpha.3",
    "seed_release_commit": "633c130187b2a2bb42f24cfd66662d475de385d2",
    "compatibility_standard": "ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3",
    "compatibility_standard_profile": "ASET-SEED-COMPATIBILITY-STANDARD-V1",
}
EXPECTED_TLAPM = {
    "required_commit": "4600b24c6d95a25ff081ad37b63b2a01c29d43a5",
    "required_version": "4600b24",
}
EXPECTED_PROOF_COUNTS = {"canon": 3, "seed": 35}
FROZEN_SEED_REPOSITORY = "https://github.com/attractor-set/" + "ASET"
EXPECTED_PROJECT_URLS = {
    "SeedSpecification": "https://github.com/attractor-set/aset-seed",
    "Repository": "https://github.com/attractor-set/aset-network",
}
FORBIDDEN_HISTORICAL_PATHS = [
    "reference/legacy_network_reference.py",
    "tools/verify_minimal_core_reduction.py",
    "tools/run_legacy_admission_refinement_tlaps.py",
    "extension/canonical/assurance/legacy-admission-refinement-proof.json",
    "extension/canonical/assurance/minimal-core-reduction.json",
    "extension/canonical/formal/NetworkLegacyAlpha2.tla",
    "extension/canonical/formal/NetworkLegacyAdmissionRefinement.tla",
    "extension/canonical/formal/NetworkLegacyAdmissionRefinementProofs.tla",
    "extension/canonical/formal/NetworkAdmissionCore.tla",
]

FORBIDDEN_PROFILE_LEAK_PATHS = [
    "extension/canonical/protocol/federation-profile.json",
    "extension/canonical/protocol/dynamic-profile-profile.json",
    "extension/canonical/conformance/federation-profile-conformance-profile.json",
    "extension/canonical/conformance/dynamic-profile-conformance-profile.json",
    "extension/canonical/formal/FederationProfile.tla",
    "extension/canonical/formal/FederationCompositionLiveness.tla",
    "extension/canonical/liveness",
]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def self_digest(path: Path, field: str) -> dict:
    data = json.loads(path.read_text())
    declared = data.pop(field)
    actual = "sha256:" + hashlib.sha256(canonical_bytes(data)).hexdigest()
    if declared != actual:
        raise SystemExit(f"self-digest mismatch: {path.relative_to(ROOT)}")
    data[field] = declared
    return data


def registry() -> tuple[Registry, dict[str, dict]]:
    resources = []
    schemas = {}
    for schema_dir in [CORE_SCHEMAS, *PROFILE_SCHEMA_DIRS]:
        for path in sorted(schema_dir.glob("*.json")):
            data = json.loads(path.read_text())
            Draft202012Validator.check_schema(data)
            resources.append((data["$id"], Resource.from_contents(data)))
            schemas[path.name] = data
    return Registry().with_resources(resources), schemas


def verify_current_federation_profile() -> None:
    profile_path = C / "profiles/federation/profile.json"
    profile = json.loads(profile_path.read_text())
    semantics = profile.get("profile_semantics", {})
    if semantics.get("network_admission_state_fields") != ["imports"]:
        raise SystemExit("federation profile Network projection mismatch")
    if semantics.get("network_projection") != (
        "FEDERATION_PROFILE_TRANSITIONS_STUTTER_ON_NETWORK_ADMISSION_STATE"
    ):
        raise SystemExit("federation profile must stutter on Network admission state")
    if set(semantics.get("profile_owned_transition_kinds", [])) != {
        "FEDERATION_GENESIS",
        "MEMBER_JOIN",
        "ROUTE_GRANT",
        "EXPORT_ARTIFACT",
        "SUSPEND_ROUTE",
        "MEMBER_WITHDRAW",
    }:
        raise SystemExit("federation transition ownership mismatch")
    if semantics.get("seed_owned_terminal_recognition") is not True:
        raise SystemExit("federation profile must not own terminal recognition")
    if profile.get("provided_capabilities") != [
        "RETAINED_EXPORT",
        "DELIVERY",
        "TARGET_OBSERVATION",
    ]:
        raise SystemExit("federation capability catalogue mismatch")

    definition_path = C / "profiles/federation/definition.json"
    definition = json.loads(definition_path.read_text())
    ok, code = validate_wire_object("PROFILE_DEFINITION", definition)
    if not ok:
        raise SystemExit(f"federation profile definition invalid: {code}")
    expected_components = {
        "parent_contract_digest": sha(C / "source/network-extension-model.json"),
        "scope_digest": sha(C / "profiles/federation/scope.json"),
        "requirements_digest": sha(C / "profiles/federation/requirements.json"),
        "invariants_digest": sha(C / "profiles/federation/invariants.json"),
    }
    for field, expected in expected_components.items():
        if definition.get(field) != expected:
            raise SystemExit(f"federation profile component digest mismatch: {field}")

    declared_schemas = {item["name"]: item for item in profile.get("wire_schemas", [])}
    actual_schemas = {
        path.name: sha(path) for path in (C / "profiles/federation/schemas").glob("*.json")
    }
    if set(declared_schemas) != set(actual_schemas):
        raise SystemExit("federation wire schema catalogue mismatch")
    for name, digest in actual_schemas.items():
        if declared_schemas[name].get("sha256") != digest:
            raise SystemExit(f"federation wire schema digest mismatch: {name}")

    safety = profile.get("assurance", {}).get("safety", {})
    for key, digest_key in [("path", "sha256"), ("config", "config_sha256")]:
        if sha(ROOT / safety[key]) != safety[digest_key]:
            raise SystemExit(f"federation profile assurance digest mismatch: {key}")


def verify_liveness_profile() -> None:
    profile = json.loads((C / "profiles/liveness/profile.json").read_text())
    if profile.get("profile_id") != "ASET-NETWORK-LIVENESS-V1":
        raise SystemExit("liveness profile identity mismatch")
    if "parent_profile" in profile:
        raise SystemExit("liveness profile must not be nested under another profile")
    claim = profile.get("claim_semantics", {})
    if (
        claim.get("claim_type") != "OPTIONAL_DYNAMIC_PROFILE"
        or claim.get("required_for_core_conformance") is not False
    ):
        raise SystemExit("liveness optional-profile claim semantics mismatch")
    composition = profile.get("composition_semantics", {})
    if composition.get("profile_parent_required") is not False:
        raise SystemExit("liveness profile must compose without a profile parent")
    if composition.get("required_profile_capabilities") != [
        "RETAINED_EXPORT",
        "DELIVERY",
        "TARGET_OBSERVATION",
    ]:
        raise SystemExit("liveness required-capability catalogue mismatch")
    resolution = profile.get("resolution_semantics", {})
    if resolution.get("resolution_owner") != "PINNED_TARGET_LOCAL_SEED" or resolution.get(
        "terminal_local_results"
    ) != ["ALLOW", "BLOCK"]:
        raise SystemExit("liveness terminal-resolution ownership mismatch")

    definition = json.loads((C / "profiles/liveness/definition.json").read_text())
    ok, code = validate_wire_object("PROFILE_DEFINITION", definition)
    if not ok:
        raise SystemExit(f"liveness profile definition invalid: {code}")
    expected_components = {
        "parent_contract_digest": sha(C / "source/network-extension-model.json"),
        "scope_digest": sha(C / "profiles/liveness/scope.json"),
        "requirements_digest": sha(C / "profiles/liveness/requirements.json"),
        "invariants_digest": sha(C / "profiles/liveness/invariants.json"),
    }
    for field, expected in expected_components.items():
        if definition.get(field) != expected:
            raise SystemExit(f"liveness profile component digest mismatch: {field}")


def verify_federation_liveness_composition() -> None:
    path = C / "assurance/profile-compositions/federation-liveness/composition.json"
    composition = json.loads(path.read_text())
    if composition.get("member_profiles") != [
        "ASET-NETWORK-FEDERATION-PROFILE-V1",
        "ASET-NETWORK-LIVENESS-V1",
    ]:
        raise SystemExit("federation+liveness composition members mismatch")
    if composition.get("profile_parent_relation") is not False:
        raise SystemExit("profile composition must not create a parent relation")
    binding = composition.get("capability_binding", {})
    if binding.get("provided") != binding.get("required"):
        raise SystemExit("federation+liveness capability binding mismatch")
    assurance = composition.get("assurance", {})
    for key, digest_key in [("path", "sha256"), ("config", "config_sha256")]:
        if sha(ROOT / assurance[key]) != assurance[digest_key]:
            raise SystemExit(f"profile-composition assurance digest mismatch: {key}")


def main() -> int:
    for relative in FORBIDDEN_HISTORICAL_PATHS:
        if (ROOT / relative).exists():
            raise SystemExit(f"historical Network compatibility artifact remains: {relative}")

    for relative in FORBIDDEN_PROFILE_LEAK_PATHS:
        if (ROOT / relative).exists():
            raise SystemExit(f"profile artifact leaked into core surface: {relative}")

    package = self_digest(C / "CANON_PACKAGE.json", "package_digest")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    project_urls = project.get("urls", {})
    if project_urls != EXPECTED_PROJECT_URLS:
        raise SystemExit("project URLs do not match direct repository topology")
    if (
        project.get("name") != "aset-network"
        or project.get("version") != "0.1.0a3"
        or project.get("description")
        != "Minimal cross-context evidence admission semantics for ASET Seed"
    ):
        raise SystemExit("project metadata does not match renamed alpha.3 project identity")
    if package["extension_version"] != "0.1.0-alpha.3" or package["canon_id"] != (
        "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3"
    ):
        raise SystemExit("package identity mismatch")

    for item in package["files"]:
        path = ROOT / item["path"]
        if not path.is_file() or sha(path) != item["sha256"]:
            raise SystemExit(f"package digest mismatch: {item['path']}")

    model = json.loads((C / "source/network-extension-model.json").read_text())
    if model["version"] != "0.1.0-alpha.3" or model["status"] != (
        "MINIMAL_ADMISSION_CORE_NORMATIVE"
    ):
        raise SystemExit("minimal core identity mismatch")
    if model["state_partition"]["semantic_state_fields"] != ["imports"] or model[
        "transition_kinds"
    ] != ["ADMIT_IMPORT"]:
        raise SystemExit("minimal core must be imports + ADMIT_IMPORT")
    non_core_transitions = {
        "RECORD_RECOGNITION",
        "FEDERATION_GENESIS",
        "MEMBER_JOIN",
        "ROUTE_GRANT",
    }
    if "recognitions" in model["state"] or any(
        transition in model["transition_kinds"] for transition in non_core_transitions
    ):
        raise SystemExit("non-core semantics leaked into Network core")

    binding = json.loads(UP.read_text())
    for key, value in EXPECTED_SEED.items():
        if binding.get(key) != value:
            raise SystemExit(f"upstream Seed binding mismatch: {key}")
    if binding.get("upstream_repository") != FROZEN_SEED_REPOSITORY:
        raise SystemExit("frozen upstream Seed repository locator mismatch")
    if (
        binding.get("compatibility") != "STRICT_EXTENSION_NO_WEAKENING"
        or binding.get("implementation_precedence") != "NONE"
    ):
        raise SystemExit("Seed compatibility boundary mismatch")

    relation = self_digest(C / "formal/canon-tla-relation.json", "relation_digest")
    if relation["profile"] != "ASET-NETWORK-CANON-TLA-PROJECTION-V3":
        raise SystemExit("formal relation profile mismatch")
    for section in ["source_model", "target_model", "seed_projection", "history_model"]:
        item = relation[section]
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise SystemExit(f"formal relation digest mismatch: {item['path']}")

    canon_projection = relation["canon_projection"]
    for key, digest_key in [("path", "sha256"), ("proof_path", "proof_sha256")]:
        if sha(ROOT / canon_projection[key]) != canon_projection[digest_key]:
            raise SystemExit(f"canon projection relation digest mismatch: {key}")

    generation = subprocess.run(
        [sys.executable, "-m", "tools.generate_canon_tla_projection", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if generation.returncode:
        raise SystemExit(generation.stdout)

    canon = json.loads((C / "assurance/canon-tla-refinement.json").read_text())
    canon_evidence = json.loads((C / "assurance/canon-refinement-proof.json").read_text())
    seed_evidence = json.loads((C / "assurance/seed-refinement-proof.json").read_text())
    for name, evidence in [("canon", canon_evidence), ("seed", seed_evidence)]:
        gate = evidence["proof_gate"]
        if evidence["status"] != "MECHANICALLY_PROVED" or gate["verdict"] != "MECHANICALLY_PROVED":
            raise SystemExit(f"{name} proof must be mechanically proved")
        if gate["obligations_proved"] != EXPECTED_PROOF_COUNTS[name]:
            raise SystemExit(f"{name} proof obligation count mismatch")
        if gate.get("materialization") != "REPRODUCED_WITH_PINNED_TLAPM":
            raise SystemExit(f"{name} proof materialization marker mismatch")
        if evidence["tlapm"] != EXPECTED_TLAPM:
            raise SystemExit(f"{name} TLAPM binding mismatch")

    for evidence_name, evidence in [("canon", canon_evidence), ("Seed", seed_evidence)]:
        for item in evidence["network_artifacts"].values():
            if item["sha256"] != sha(ROOT / item["path"]):
                raise SystemExit(f"{evidence_name} proof artifact digest mismatch: {item['path']}")

    if (
        canon["generated_projection"]["profile"] != "ASET-NETWORK-CANON-TLA-PROJECTION-V3"
        or canon["source_model"]["sha256"] != sha(C / "source/network-extension-model.json")
        or canon["target_model"]["sha256"] != sha(C / "formal/NetworkExtension.tla")
    ):
        raise SystemExit("canon refinement binding mismatch")
    if (
        canon["status"] != "MECHANICALLY_PROVED"
        or canon["proof_evidence"].get("status") != "MECHANICALLY_PROVED"
        or canon["proof_evidence"].get("obligations_proved") != 3
    ):
        raise SystemExit("canon refinement materialization mismatch")

    if (
        relation["canon_projection"].get("status") != "MECHANICALLY_PROVED"
        or relation["canon_projection"].get("obligations_proved") != 3
    ):
        raise SystemExit("formal relation canon proof status/count mismatch")
    if (
        relation["seed_refinement"].get("status") != "MECHANICALLY_PROVED"
        or relation["seed_refinement"].get("obligations_proved") != 35
    ):
        raise SystemExit("formal relation Seed proof status/count mismatch")
    if "legacy_alpha2_refinement" in relation:
        raise SystemExit("historical Network refinement must not remain in current relation")

    if "federation_assurance" in relation or "federation_lifecycle" in relation.get(
        "projection_surfaces", {}
    ):
        raise SystemExit("profile assurance must not be embedded in the core formal relation")

    harness = relation.get("tlc_harness", {})
    if harness.get("module") != "NetworkExtensionTLC" or harness.get("properties") != [
        "ImportsAppendOnlyTemporal"
    ]:
        raise SystemExit("TLC temporal harness relation mismatch")
    for key, digest_key in [("path", "sha256"), ("config", "config_sha256")]:
        if sha(ROOT / harness[key]) != harness[digest_key]:
            raise SystemExit(f"TLC temporal harness digest mismatch: {key}")

    harness_text = (C / "formal/NetworkExtensionTLC.tla").read_text()
    if "ImportsAppendOnlyTemporal == [][ImportsAppendOnly]_vars" not in harness_text:
        raise SystemExit("TLC append-only property must temporalize the normative action predicate")
    base_config = (C / "formal/NetworkExtension.cfg").read_text()
    harness_config = (C / "formal/NetworkExtensionTLC.cfg").read_text()
    if "PROPERTIES" in base_config or "ImportsAppendOnlyTemporal" not in harness_config:
        raise SystemExit("TLC property must live only in the temporal harness config")

    schema_registry, schemas = registry()
    protocol = json.loads((C / "protocol/protocol-profile.json").read_text())
    expected_profile_catalog = [
        {
            "profile_id": "ASET-NETWORK-DYNAMIC-PROFILES-V1",
            "path": "extension/canonical/profiles/dynamic/profile.json",
        },
        {
            "profile_id": "ASET-NETWORK-FEDERATION-PROFILE-V1",
            "path": "extension/canonical/profiles/federation/profile.json",
        },
        {
            "profile_id": "ASET-NETWORK-LIVENESS-V1",
            "path": "extension/canonical/profiles/liveness/profile.json",
        },
    ]
    if protocol.get("optional_profile_catalog") != expected_profile_catalog:
        raise SystemExit("protocol direct profile catalogue mismatch")
    actual = {path.name: sha(path) for path in CORE_SCHEMAS.glob("*.json")}
    if (
        protocol["schema_count"] != len(actual)
        or {item["name"]: item["sha256"] for item in protocol["schemas"]} != actual
    ):
        raise SystemExit("protocol schema catalogue mismatch")
    if any(item.get("owner") == "LEGACY_ONLY_SEED_DERIVED" for item in protocol["schemas"]):
        raise SystemExit("legacy-only wire schema remains in current protocol")

    core = json.loads((C / "conformance/conformance-profile.json").read_text())
    if core["profile_id"] != "ASET-NETWORK-EXTENSION-CONFORMANCE-V2" or core["case_count"] != 4:
        raise SystemExit("core conformance identity/count mismatch")
    core_validator = Draft202012Validator(
        schemas["conformance-case.schema.json"], registry=schema_registry
    )
    for item in core["cases"]:
        path = ROOT / item["path"]
        case = json.loads(path.read_text())
        errors = list(core_validator.iter_errors(case))
        if errors:
            raise SystemExit(
                f"core conformance schema invalid: {item['case_id']}: {errors[0].message}"
            )
        if item["sha256"] != sha(path):
            raise SystemExit(f"core conformance digest mismatch: {item['case_id']}")

    dynamic_failures = run_profile_conformance()
    if dynamic_failures:
        raise SystemExit(f"dynamic-profile conformance failed: {dynamic_failures[0][0]}")

    verify_current_federation_profile()
    verify_liveness_profile()
    verify_federation_liveness_composition()
    federation = json.loads((C / "profiles/federation/conformance/profile.json").read_text())
    if federation["case_count"] != 10 or federation.get("source_semantics") != (
        "NATIVE_FEDERATION_PROFILE_CASES"
    ):
        raise SystemExit("federation profile conformance identity/count mismatch")
    for item in federation["cases"]:
        if "/profiles/federation/conformance/cases/" not in item["path"]:
            raise SystemExit(f"federation case is not native: {item['case_id']}")
        path = ROOT / item["path"]
        if item["sha256"] != sha(path):
            raise SystemExit(f"federation conformance digest mismatch: {item['case_id']}")
        case = json.loads(path.read_text())
        if case["case_id"] != item["case_id"]:
            raise SystemExit(f"federation case identity mismatch: {item['case_id']}")
        _, actual_result = execute_federation_case(case)
        if actual_result != case["expected"]:
            raise SystemExit(f"federation conformance failed: {item['case_id']}")

    print(f"OK: package files={len(package['files'])}")
    print(f"OK: package digest={package['package_digest']}")
    print("OK: Seed compatibility binding exact")
    print("OK: normative Network core state_fields=1 transition_kinds=1")
    print("OK: canon-to-TLA alpha.3 relation exact")
    print(f"OK: canon TLAPS status={canon_evidence['status']}")
    print(f"OK: Seed TLAPS status={seed_evidence['status']}")
    print("OK: current canonical surface contains no historical compatibility artifacts")
    print("OK: federation profile is self-contained")
    print("OK: liveness profile is independent")
    print("OK: federation+liveness composition is explicit assurance")
    print("OK: dynamic profiles add no Network state or transitions")
    print("OK: schemas valid")
    print("OK: core conformance cases=4")
    print("OK: dynamic-profile conformance cases=8")
    print("OK: federation-profile conformance cases=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
