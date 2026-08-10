from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tools.dynamic_profile_conformance import run_profile_conformance, validate_wire_object
from tools.verify_minimal_core_reduction import (
    verify_conformance_trace_projection,
    verify_decomposition,
    verify_profile_definition,
)

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "extension/canonical"
S = C / "protocol/schemas"
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
EXPECTED_PROOF_COUNTS = {"canon": 3, "seed": 35, "legacy": 23}


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
    for path in sorted(S.glob("*.json")):
        data = json.loads(path.read_text())
        Draft202012Validator.check_schema(data)
        resources.append((data["$id"], Resource.from_contents(data)))
        schemas[path.name] = data
    return Registry().with_resources(resources), schemas


def main() -> int:
    package = self_digest(C / "CANON_PACKAGE.json", "package_digest")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    if project.get("version") != "0.1.0a3" or project.get("description") != (
        "Minimal cross-context evidence admission extension for ASET Seed"
    ):
        raise SystemExit("project metadata does not match alpha.3 minimal admission release")
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
        "MINIMAL_ADMISSION_CORE_ALPHA3_NORMATIVE_CUTOVER"
    ):
        raise SystemExit("minimal core identity mismatch")
    if model["state_partition"]["semantic_state_fields"] != ["imports"] or model[
        "transition_kinds"
    ] != ["ADMIT_IMPORT"]:
        raise SystemExit("minimal core must be imports + ADMIT_IMPORT")
    legacy_transitions = {
        "RECORD_RECOGNITION",
        "FEDERATION_GENESIS",
        "MEMBER_JOIN",
        "ROUTE_GRANT",
    }
    if "recognitions" in model["state"] or any(
        transition in model["transition_kinds"] for transition in legacy_transitions
    ):
        raise SystemExit("legacy semantics leaked into core")

    binding = json.loads(UP.read_text())
    for key, value in EXPECTED_SEED.items():
        if binding.get(key) != value:
            raise SystemExit(f"upstream Seed binding mismatch: {key}")
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
        path = ROOT / item["path"]
        if sha(path) != item["sha256"]:
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
    legacy_evidence = json.loads(
        (C / "assurance/legacy-admission-refinement-proof.json").read_text()
    )
    evidence_sets = [
        ("canon", canon_evidence),
        ("seed", seed_evidence),
        ("legacy", legacy_evidence),
    ]
    for name, evidence in evidence_sets:
        gate = evidence["proof_gate"]
        if evidence["status"] != "MECHANICALLY_PROVED" or gate["verdict"] != "MECHANICALLY_PROVED":
            raise SystemExit(f"{name} proof must be mechanically proved")
        if gate["obligations_proved"] != EXPECTED_PROOF_COUNTS[name]:
            raise SystemExit(f"{name} proof obligation count mismatch")
        if gate.get("materialization") != "REPRODUCED_WITH_PINNED_TLAPM":
            raise SystemExit(f"{name} proof materialization marker mismatch")
        if evidence["tlapm"] != EXPECTED_TLAPM:
            raise SystemExit(f"{name} TLAPM binding mismatch")

    for item in canon_evidence["network_artifacts"].values():
        if item["sha256"] != sha(ROOT / item["path"]):
            raise SystemExit(f"canon proof artifact digest mismatch: {item['path']}")
    for item in seed_evidence["network_artifacts"].values():
        if item["sha256"] != sha(ROOT / item["path"]):
            raise SystemExit(f"Seed proof artifact digest mismatch: {item['path']}")
    for item in legacy_evidence["artifacts"].values():
        if item["sha256"] != sha(ROOT / item["path"]):
            raise SystemExit(f"legacy proof artifact digest mismatch: {item['path']}")

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

    reduction = json.loads((C / "assurance/minimal-core-reduction.json").read_text())
    normative_core = reduction.get("normative_core", {})
    if normative_core.get("semantic_state_fields") != ["imports"] or normative_core.get(
        "transition_kinds"
    ) != ["ADMIT_IMPORT"]:
        raise SystemExit("minimal-core reduction metadata still uses non-normative/shadow core")
    verification = reduction["verification"]
    if (
        verification.get("legacy_tlaps_status") != "MECHANICALLY_PROVED"
        or verification.get("legacy_tlaps_obligations_proved") != 23
    ):
        raise SystemExit("minimal-core legacy proof materialization mismatch")

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
    if (
        relation["legacy_alpha2_refinement"].get("status") != "MECHANICALLY_PROVED"
        or relation["legacy_alpha2_refinement"].get("obligations_proved") != 23
    ):
        raise SystemExit("formal relation legacy proof status/count mismatch")

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

    liveness = json.loads((C / "liveness/liveness-profile.json").read_text())
    if liveness.get("parent_profile") != "ASET-NETWORK-FEDERATION-PROFILE-V1":
        raise SystemExit("liveness parent profile mismatch")
    resolution = liveness.get("resolution_semantics", {})
    if (
        resolution.get("resolution_owner") != "PINNED_TARGET_LOCAL_SEED"
        or resolution.get("terminal_local_results") != ["ALLOW", "BLOCK"]
        or resolution.get("legacy_assurance_projection") != {"ACCEPT": "ALLOW", "DENY": "BLOCK"}
    ):
        raise SystemExit("liveness terminal-resolution ownership/projection mismatch")
    if not any(
        assumption.get("id") == "NET-LIVE-A-003"
        and assumption.get("name") == "TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION"
        for assumption in liveness.get("assumptions", [])
    ):
        raise SystemExit("liveness Seed progress assumption mismatch")

    schema_registry, schemas = registry()
    protocol = json.loads((C / "protocol/protocol-profile.json").read_text())
    actual = {path.name: sha(path) for path in S.glob("*.json")}
    if (
        protocol["schema_count"] != len(actual)
        or {item["name"]: item["sha256"] for item in protocol["schemas"]} != actual
    ):
        raise SystemExit("protocol schema catalogue mismatch")

    core = json.loads((C / "conformance/conformance-profile.json").read_text())
    if core["profile_id"] != "ASET-NETWORK-EXTENSION-CONFORMANCE-V2" or core["case_count"] != 4:
        raise SystemExit("core conformance identity/count mismatch")
    validator = Draft202012Validator(
        schemas["conformance-case.schema.json"],
        registry=schema_registry,
    )
    for item in core["cases"]:
        path = ROOT / item["path"]
        case = json.loads(path.read_text())
        errors = list(validator.iter_errors(case))
        if errors:
            raise SystemExit(
                f"core conformance schema invalid: {item['case_id']}: {errors[0].message}"
            )
        if item["sha256"] != sha(path):
            raise SystemExit(f"core conformance digest mismatch: {item['case_id']}")

    dynamic_failures = run_profile_conformance()
    if dynamic_failures:
        raise SystemExit(f"dynamic-profile conformance failed: {dynamic_failures[0][0]}")

    verify_profile_definition()
    verify_decomposition()
    legacy_count = verify_conformance_trace_projection()
    federation = json.loads(
        (C / "conformance/federation-profile-conformance-profile.json").read_text()
    )
    if federation["case_count"] != 10:
        raise SystemExit("federation profile conformance count mismatch")
    for item in federation["cases"]:
        if item["sha256"] != sha(ROOT / item["path"]):
            raise SystemExit(f"federation legacy digest mismatch: {item['case_id']}")

    definition = json.loads(
        (C / "protocol/profiles/federation-profile-definition.json").read_text()
    )
    ok, code = validate_wire_object("PROFILE_DEFINITION", definition)
    if not ok:
        raise SystemExit(f"federation profile definition invalid after cutover: {code}")
    if definition["parent_contract_digest"] != sha(C / "source/network-extension-model.json"):
        raise SystemExit("federation profile parent digest mismatch")

    print(f"OK: package files={len(package['files'])}")
    print(f"OK: package digest={package['package_digest']}")
    print("OK: Seed compatibility binding exact")
    print("OK: normative Network core state_fields=1 transition_kinds=1")
    print("OK: canon-to-TLA alpha.3 relation exact")
    print(f"OK: canon TLAPS status={canon_evidence['status']}")
    print(f"OK: Seed TLAPS status={seed_evidence['status']}")
    print(f"OK: legacy->minimal TLAPS status={legacy_evidence['status']}")
    print("OK: dynamic profiles add no Network state or transitions")
    print("OK: schemas valid")
    print("OK: core conformance cases=4")
    print("OK: dynamic-profile conformance cases=8")
    print("OK: federation-profile conformance cases=10")
    print(f"OK: legacy reduction conformance traces={legacy_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
