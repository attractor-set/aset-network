from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
FORMAL_RELATION = CANON / "formal/canon-tla-relation.json"
LIVENESS_PROFILE = CANON / "liveness/liveness-profile.json"
SEED_REFINEMENT_EVIDENCE = CANON / "assurance/seed-refinement-proof.json"
UPSTREAM_BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"

EXPECTED_SEED = {
    "canon_id": "ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1",
    "canon_version": "0.3.0-alpha.1",
    "canon_package_digest": (
        "sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31"
    ),
    "compatibility_standard": "ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3",
    "compatibility_standard_profile": "ASET-SEED-COMPATIBILITY-STANDARD-V1",
    "seed_conformance_kit_sha256": (
        "sha256:5ecf9b93377a062b8772b4b4b44b4d76a0997d8ba98e8711e717456abbe583db"
    ),
    "seed_release_commit": "633c130187b2a2bb42f24cfd66662d475de385d2",
    "seed_release_tag": "seed-0.3.0-alpha.3",
}


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def verify_self_digest(path: Path, field: str) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    declared = data.pop(field)
    actual = "sha256:" + hashlib.sha256(canonical_bytes(data)).hexdigest()
    if actual != declared:
        raise SystemExit(f"self-digest mismatch: {path.relative_to(ROOT)}")
    data[field] = declared
    return data


def main() -> int:
    package = verify_self_digest(CANON / "CANON_PACKAGE.json", "package_digest")

    for item in package["files"]:
        path = ROOT / item["path"]
        if not path.is_file():
            raise SystemExit(f"missing package file: {item['path']}")
        if sha(path) != item["sha256"]:
            raise SystemExit(f"digest mismatch: {item['path']}")

    binding = json.loads(UPSTREAM_BINDING.read_text(encoding="utf-8"))
    for key, expected in EXPECTED_SEED.items():
        if binding.get(key) != expected:
            raise SystemExit(f"upstream Seed binding mismatch: {key}")
    if binding.get("compatibility") != "STRICT_EXTENSION_NO_WEAKENING":
        raise SystemExit("upstream Seed compatibility mode mismatch")
    if binding.get("implementation_precedence") != "NONE":
        raise SystemExit("implementation precedence must remain NONE")

    relation = verify_self_digest(FORMAL_RELATION, "relation_digest")
    for section, digest_field in (
        ("source_model", "sha256"),
        ("target_model", "sha256"),
        ("seed_projection", "sha256"),
        ("history_model", "sha256"),
    ):
        item = relation[section]
        path = ROOT / item["path"]
        if sha(path) != item[digest_field]:
            raise SystemExit(f"formal relation digest mismatch: {item['path']}")
    for section, path_field, digest_field in (
        ("safety_model", "config", "sha256"),
        ("history_model", "config", "config_sha256"),
        ("liveness_model", "profile_path", "profile_sha256"),
        ("liveness_model", "config", "config_sha256"),
    ):
        item = relation[section]
        path = ROOT / item[path_field]
        if sha(path) != item[digest_field]:
            raise SystemExit(f"formal relation digest mismatch: {item[path_field]}")

    if (
        relation["upstream_seed"]["compatibility_standard"]
        != EXPECTED_SEED["compatibility_standard"]
    ):
        raise SystemExit("formal relation is not pinned to the current Seed Compatibility Standard")
    if (
        relation["upstream_seed"]["seed_canon_tla_projection_profile"]
        != "ASET-SEED-CANON-TLA-PROJECTION-V5"
    ):
        raise SystemExit("formal relation Seed canon-to-TLA profile mismatch")

    liveness = json.loads(LIVENESS_PROFILE.read_text(encoding="utf-8"))
    if liveness.get("profile_id") != "ASET-NETWORK-LIVENESS-V1":
        raise SystemExit("liveness profile mismatch")
    if liveness.get("normative") is not True:
        raise SystemExit("liveness profile must be explicitly normative")
    if len(liveness.get("assumptions", [])) != 4 or len(liveness.get("guarantees", [])) != 3:
        raise SystemExit("liveness profile coverage mismatch")
    claim = liveness.get("claim_semantics", {})
    if claim.get("claim_type") != "OPTIONAL_CAPABILITY_CLAIM":
        raise SystemExit("liveness claim type mismatch")
    if claim.get("required_for_core_conformance") is not False:
        raise SystemExit("liveness must remain optional for core conformance")
    if claim.get("assumptions_must_be_declared") is not True:
        raise SystemExit("liveness assumptions must be declared")
    resolution = liveness.get("resolution_semantics", {})
    if set(resolution.get("terminal_local_results", [])) != {"ACCEPT", "DENY"}:
        raise SystemExit("liveness terminal local resolution mismatch")
    if resolution.get("eventual_accept_required") is not False:
        raise SystemExit("liveness must not require eventual ACCEPT")
    if resolution.get("global_agreement_required") is not False:
        raise SystemExit("liveness must not require global agreement")
    if resolution.get("unconditional_transport_guarantee") is not False:
        raise SystemExit("liveness must not claim unconditional transport")

    model = json.loads((CANON / "source/network-extension-model.json").read_text(encoding="utf-8"))
    formal_assurance = model.get("formal_assurance", {})
    if formal_assurance.get("seed_refinement_proof_evidence") != (
        "extension/canonical/assurance/seed-refinement-proof.json"
    ):
        raise SystemExit("network model Seed refinement evidence binding mismatch")
    if formal_assurance.get("seed_refinement_proof_runner") != (
        "tools/run_seed_refinement_tlaps.py"
    ):
        raise SystemExit("network model Seed refinement proof runner mismatch")

    state_fields = set(model.get("state", {}))
    partition = model.get("state_partition", {})
    semantic_fields = set(partition.get("semantic_state_fields", []))
    history_fields = set(partition.get("evidence_history_fields", []))
    if semantic_fields & history_fields:
        raise SystemExit("network state partition overlaps")
    if semantic_fields | history_fields != state_fields:
        raise SystemExit("network state partition is not exhaustive")
    if history_fields != {"history"}:
        raise SystemExit("network evidence history partition mismatch")
    if partition.get("evidence_history_role") != "NORMATIVE_APPEND_ONLY_EVIDENCE_TRACE":
        raise SystemExit("network evidence history role mismatch")
    if "MUST NOT itself confer Authority" not in partition.get("transition_enabling_rule", ""):
        raise SystemExit("network evidence history authority boundary missing")

    conformance = json.loads(
        (CANON / "conformance/conformance-profile.json").read_text(encoding="utf-8")
    )
    optional_profiles = {
        item["profile_id"]: item
        for item in conformance.get("optional_claim_profiles", [])
    }
    live_claim = optional_profiles.get("ASET-NETWORK-LIVENESS-V1")
    if live_claim is None:
        raise SystemExit("core conformance does not expose the optional liveness claim profile")
    if live_claim.get("required_for_core_conformance") is not False:
        raise SystemExit("core conformance incorrectly requires liveness")
    if live_claim.get("normative_when_claimed") is not True:
        raise SystemExit("claimed liveness profile must remain normative")

    surfaces = relation.get("projection_surfaces", {})
    if surfaces.get("semantic_state", {}).get("formal_model") != "NetworkExtension":
        raise SystemExit("semantic-state formal projection mismatch")
    if surfaces.get("evidence_history", {}).get("formal_model") != "NetworkHistory":
        raise SystemExit("evidence-history formal projection mismatch")
    if (
        surfaces.get("conditional_liveness", {}).get("scope")
        != "ASET-NETWORK-LIVENESS-V1"
    ):
        raise SystemExit("liveness formal projection mismatch")
    if relation.get("liveness_model", {}).get("required_for_core_conformance") is not False:
        raise SystemExit("formal relation incorrectly requires liveness for core conformance")

    invariant_ids = {item["id"] for item in model["invariants"]}
    relation_invariant_ids = {item["id"] for item in relation["invariant_coverage"]}
    if invariant_ids != relation_invariant_ids:
        raise SystemExit("canon-to-TLA invariant coverage mismatch")

    resources = []
    by_name = {}
    schema_dir = CANON / "protocol/schemas"
    for path in schema_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(data)
        resources.append((data["$id"], Resource.from_contents(data)))
        by_name[path.name] = data
    registry = Registry().with_resources(resources)

    validator = Draft202012Validator(by_name["conformance-case.schema.json"], registry=registry)
    for path in (CANON / "conformance/cases").rglob("*.json"):
        validator.validate(json.loads(path.read_text(encoding="utf-8")))

    print(f"OK: package files={len(package['files'])}")
    print(f"OK: package digest={package['package_digest']}")
    print("OK: Seed compatibility binding exact")
    print("OK: canon-to-TLA relation exact")
    print("OK: semantic state / evidence history partition exact")
    print("OK: optional conditional liveness claim exact")
    print("OK: liveness profile exact")
    refinement = relation.get("seed_refinement", {})
    expected_seed_resolution_sha = (
        "sha256:1c0ebb27ed52da289f0981dcb11b61b6"
        "a7fc5c4a030ba434ae0b1d53b286b926"
    )
    if refinement.get("mapping_module") != "NetworkExtensionSeedRefinement":
        raise SystemExit("ERROR: Seed refinement mapping module mismatch")
    if refinement.get("proof_module") != "NetworkExtensionSeedRefinementProofs":
        raise SystemExit("ERROR: Seed refinement proof module mismatch")
    if refinement.get("upstream_module") != "SeedResolution":
        raise SystemExit("ERROR: Seed refinement upstream module mismatch")
    if refinement.get("upstream_sha256") != expected_seed_resolution_sha:
        raise SystemExit("ERROR: pinned SeedResolution digest mismatch")
    if refinement.get("status") != "MECHANICALLY_PROVED":
        raise SystemExit("ERROR: Seed refinement must be mechanically proved")
    if (
        relation.get("seed_projection", {}).get("exact_seed_tlaps_refinement")
        != "MECHANICALLY_PROVED"
    ):
        raise SystemExit("ERROR: Seed projection proof status mismatch")
    for field in ("mapping_path", "proof_path"):
        target = ROOT / refinement[field]
        if not target.is_file():
            raise SystemExit(f"ERROR: missing Seed refinement artifact: {target}")

    evidence = json.loads(SEED_REFINEMENT_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("status") != "MECHANICALLY_PROVED":
        raise SystemExit("ERROR: Seed refinement evidence status mismatch")
    if evidence.get("scope") != "PINNED_SEED_REFINEMENT":
        raise SystemExit("ERROR: Seed refinement evidence scope mismatch")
    gate = evidence.get("proof_gate", {})
    if gate.get("verdict") != "PASS":
        raise SystemExit("ERROR: Seed refinement evidence verdict mismatch")
    if gate.get("obligations_proved") != 261:
        raise SystemExit("ERROR: Seed refinement evidence obligation count mismatch")
    if gate.get("obligation_count_semantics") != "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT":
        raise SystemExit("ERROR: Seed refinement obligation-count semantics mismatch")
    if gate.get("final_theorems") != refinement.get("final_theorems"):
        raise SystemExit("ERROR: Seed refinement theorem evidence mismatch")
    if evidence.get("tlapm", {}).get("commit") != "4600b24c6d95a25ff081ad37b63b2a01c29d43a5":
        raise SystemExit("ERROR: Seed refinement TLAPM commit mismatch")
    if evidence.get("tlapm", {}).get("version") != "4600b24":
        raise SystemExit("ERROR: Seed refinement TLAPM version mismatch")
    upstream = evidence.get("upstream_seed", {})
    if upstream.get("release_commit") != EXPECTED_SEED["seed_release_commit"]:
        raise SystemExit("ERROR: Seed refinement evidence release commit mismatch")
    if upstream.get("sha256") != expected_seed_resolution_sha:
        raise SystemExit("ERROR: Seed refinement evidence SeedResolution digest mismatch")
    artifacts = evidence.get("network_artifacts", {})
    for relation_field, evidence_key in (("mapping_path", "mapping"), ("proof_path", "proof")):
        artifact = artifacts.get(evidence_key, {})
        if artifact.get("path") != refinement.get(relation_field):
            raise SystemExit(f"ERROR: Seed refinement evidence path mismatch: {evidence_key}")
        target = ROOT / artifact["path"]
        if artifact.get("sha256") != sha(target):
            raise SystemExit(f"ERROR: Seed refinement evidence digest mismatch: {evidence_key}")
    if refinement.get("proof_evidence_path") != (
        SEED_REFINEMENT_EVIDENCE.relative_to(ROOT).as_posix()
    ):
        raise SystemExit("ERROR: Seed refinement evidence path mismatch")
    if refinement.get("proof_evidence_sha256") != sha(SEED_REFINEMENT_EVIDENCE):
        raise SystemExit("ERROR: Seed refinement evidence digest mismatch")
    if refinement.get("obligations_proved") != gate.get("obligations_proved"):
        raise SystemExit("ERROR: Seed refinement relation obligation evidence mismatch")
    print("OK: Seed TLAPS refinement mechanically proved")
    print("OK: schemas valid")
    print("OK: conformance cases valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
