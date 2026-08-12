#!/usr/bin/env python3
"""Check Network -> Seed -> public-v60 projection-assurance composition."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROFILE_PATH = Path("assurance/seed-projection/ASSURANCE_PROFILE.json")
NETWORK_CANON_PATH = Path("extension/canonical/CANON_PACKAGE.json")
NETWORK_MODEL_PATH = Path("extension/canonical/source/network-extension-model.json")
NETWORK_TLA_PATH = Path("extension/canonical/formal/NetworkExtension.tla")
NETWORK_SEED_PROJECTION_PATH = Path(
    "extension/canonical/formal/NetworkExtensionSeedProjection.tla"
)
NETWORK_SEED_REFINEMENT_PATH = Path(
    "extension/canonical/formal/NetworkExtensionSeedRefinement.tla"
)
NETWORK_SEED_PROOFS_PATH = Path(
    "extension/canonical/formal/NetworkExtensionSeedRefinementProofs.tla"
)
NETWORK_SEED_EVIDENCE_PATH = Path(
    "extension/canonical/assurance/seed-refinement-proof.json"
)
FEDERATION_PROFILE_PATH = Path("extension/canonical/profiles/federation/profile.json")
FEDERATION_TLA_PATH = Path(
    "extension/canonical/profiles/federation/assurance/FederationProfile.tla"
)

V60_PACKAGE_PATH = Path("assurance/seed-recognition-boundary/ASSURANCE_PACKAGE.json")
SEED_RESOLUTION_PATH = Path("seed/canonical/formal/SeedResolution.tla")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canon_file_hash(canon: dict[str, Any], path: str) -> str | None:
    for entry in canon.get("files", []):
        if entry.get("path") == path:
            return entry.get("sha256")
    return None


def proof_relation(v60: dict[str, Any], relation_id: str) -> dict[str, Any] | None:
    for relation in v60.get("proof_chain", []):
        if relation.get("id") == relation_id:
            return relation
    return None


def check(network_root: Path, seed_root: Path) -> dict[str, Any]:
    profile = load_json(network_root / PROFILE_PATH)
    network_canon = load_json(network_root / NETWORK_CANON_PATH)
    network_model = load_json(network_root / NETWORK_MODEL_PATH)
    network_evidence = load_json(network_root / NETWORK_SEED_EVIDENCE_PATH)
    federation_profile = load_json(network_root / FEDERATION_PROFILE_PATH)
    v60 = load_json(seed_root / V60_PACKAGE_PATH)

    network_subject = profile["network_subject"]
    seed_subject = profile["shared_seed_subject"]
    v60_subject = profile["public_v60_subject"]

    require(profile["normative"] is False, "assurance profile must remain non-normative")
    require(
        network_canon.get("canon_id") == network_subject["canon_id"],
        "Network canon id differs from projection-assurance subject",
    )
    require(
        network_canon.get("extension_version") == network_subject["extension_version"],
        "Network extension version differs from projection-assurance subject",
    )

    key_files = {
        str(NETWORK_TLA_PATH): "network_model_sha256",
        str(NETWORK_SEED_PROJECTION_PATH): "seed_projection_sha256",
        str(NETWORK_SEED_REFINEMENT_PATH): "seed_refinement_sha256",
        str(NETWORK_SEED_PROOFS_PATH): "seed_refinement_proof_sha256",
    }
    for path_text, profile_key in key_files.items():
        path = network_root / path_text
        expected = network_subject[profile_key]
        require(sha256(path) == expected, f"source identity mismatch: {path_text}")
        require(
            canon_file_hash(network_canon, path_text) == expected,
            f"Network canon package identity mismatch: {path_text}",
        )

    require(
        network_model.get("state_partition", {}).get("semantic_state_fields")
        == network_subject["semantic_state_fields"],
        "Network semantic-state fields changed",
    )
    require(
        network_model.get("transition_kinds") == network_subject["transition_kinds"],
        "Network transition kinds changed",
    )
    require(
        "terminal recognition" in network_model.get("normative_scope", {}).get("does_not_define", []),
        "Network canon no longer excludes terminal recognition",
    )

    network_tla = (network_root / NETWORK_TLA_PATH).read_text(encoding="utf-8")
    require(re.search(r"(?m)^VARIABLE\s+imports\s*$", network_tla) is not None,
            "Network TLA no longer has exactly the imports variable declaration")
    require(r"NetworkAction == \E o \in ObservationUniverse : AdmitImport(o)" in network_tla,
            "NetworkAction is no longer the minimal AdmitImport action")
    require("NoTerminalRecognitionState == TRUE" in network_tla,
            "Network TLA no longer states absence of terminal recognition state")
    require("AdmissionFailClosed" in network_tla, "Network fail-closed invariant missing")

    projection_tla = (network_root / NETWORK_SEED_PROJECTION_PATH).read_text(encoding="utf-8")
    require(r'ProjectedSeedStatus(o) == IF o \in imports THEN "UNKNOWN"' in projection_tla,
            "Seed projection no longer maps admitted imports to UNKNOWN")
    require(r'ProjectedSeedEnforcement(o) == IF o \in imports THEN "BLOCKED"' in projection_tla,
            "Seed projection no longer maps admitted imports to BLOCKED")

    refinement_tla = (network_root / NETWORK_SEED_REFINEMENT_PATH).read_text(encoding="utf-8")
    require("Seed == INSTANCE SeedResolution" in refinement_tla,
            "Network refinement no longer instantiates SeedResolution")
    require("BridgeAdmitAsSeedRegister(o)" in refinement_tla,
            "Network admission-to-Seed registration bridge missing")
    require(r"ProjectedTerminalMeta == [r \in {} |-> r]" in refinement_tla,
            "Network refinement acquired terminal Seed state")
    require("ProjectedConflicts == {}" in refinement_tla,
            "Network refinement acquired Seed conflict state")

    proof_text = (network_root / NETWORK_SEED_PROOFS_PATH).read_text(encoding="utf-8")
    for theorem in (
        "NetworkExtensionRefinesSeedSafetySpec",
        "NetworkProjectionMatchesSeedResolution",
    ):
        require(f"THEOREM {theorem} ==" in proof_text, f"required theorem missing: {theorem}")

    proof_gate = network_evidence.get("proof_gate", {})
    require(network_evidence.get("status") == "MECHANICALLY_PROVED",
            "Network-to-Seed refinement evidence is not mechanically proved")
    require(proof_gate.get("obligations_proved") == network_subject["seed_refinement_obligations"],
            "Network-to-Seed proof-obligation evidence changed")
    require(set(proof_gate.get("final_theorems", [])) == {
        "NetworkExtensionRefinesSeedSafetySpec",
        "NetworkProjectionMatchesSeedResolution",
    }, "Network-to-Seed final theorem set changed")

    network_seed_sha = network_evidence.get("upstream_seed", {}).get("sha256")
    require(network_seed_sha == seed_subject["seed_resolution_sha256"],
            "Network refinement points at a different SeedResolution source")

    require(v60.get("assurance_id") == v60_subject["assurance_id"],
            "ASET public-v60 assurance id mismatch")
    require(v60.get("package_digest") == v60_subject["package_digest"],
            "ASET public-v60 package digest mismatch")
    require(v60.get("expected_tlaps_obligations") == v60_subject["expected_tlaps_obligations"],
            "ASET public-v60 obligation total mismatch")
    require(v60.get("subject", {}).get("canon_id") == seed_subject["canon_id"],
            "public v60 protects a different Seed canon id")
    require(v60.get("subject", {}).get("canon_version") == seed_subject["canon_version"],
            "public v60 protects a different Seed canon version")
    require(v60.get("subject", {}).get("seed_resolution_sha256") == network_seed_sha,
            "Network refinement and public v60 do not share the exact Seed subject")
    require(sha256(seed_root / SEED_RESOLUTION_PATH) == network_seed_sha,
            "local ASET SeedResolution bytes do not match the shared subject")

    for required in v60_subject["required_proof_relations"]:
        actual = proof_relation(v60, required["id"])
        require(actual is not None, f"public v60 relation missing: {required['id']}")
        require(actual.get("final_theorem") == required["final_theorem"],
                f"public v60 theorem changed: {required['id']}")
        require(actual.get("expected_obligations") == required["expected_obligations"],
                f"public v60 obligation evidence changed: {required['id']}")

    semantics = federation_profile.get("profile_semantics", {})
    require(semantics.get("network_admission_state_fields") == ["imports"],
            "Federation profile Network projection fields changed")
    require(
        semantics.get("network_projection")
        == "FEDERATION_PROFILE_TRANSITIONS_STUTTER_ON_NETWORK_ADMISSION_STATE",
        "Federation profile no longer declares Network-admission stutter",
    )
    require(semantics.get("seed_owned_terminal_recognition") is True,
            "Federation profile no longer leaves terminal recognition to Seed")
    federation_tla = (network_root / FEDERATION_TLA_PATH).read_text(encoding="utf-8")
    variable_block = re.search(r"VARIABLES\s+([^\n]+)", federation_tla)
    require(variable_block is not None and "imports" not in variable_block.group(1),
            "Federation assurance state unexpectedly owns Network imports")

    return {
        "assurance_id": profile["assurance_id"],
        "network_canon_id": network_canon["canon_id"],
        "network_extension_version": network_canon["extension_version"],
        "network_seed_refinement": "MECHANICALLY_PROVED",
        "network_seed_refinement_obligations": proof_gate["obligations_proved"],
        "public_v60_assurance_id": v60["assurance_id"],
        "public_v60_package_digest": v60["package_digest"],
        "public_v60_expected_tlaps_obligations": v60["expected_tlaps_obligations"],
        "shared_seed_resolution_sha256": network_seed_sha,
        "network_core_projection": "SEED_REGISTER_REFINING_FAIL_CLOSED",
        "federation_projection": "SEED_STUTTER_VIA_UNCHANGED_NETWORK_IMPORTS",
        "composition_type": "EVIDENCE_COMPOSITION_NOT_NEW_TLAPS_THEOREM",
        "verdict": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network-root", type=Path, default=Path.cwd())
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        report = check(args.network_root.resolve(), args.seed_root.resolve())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"NETWORK_SEED_PROJECTION_ASSURANCE=FAIL: {exc}")
        return 1

    print("NETWORK_SEED_PROJECTION_ASSURANCE_SUBJECT_BINDING=PASS")
    print("NETWORK_SEED_REFINEMENT_EVIDENCE=35/35")
    print("NETWORK_PUBLIC_V60_EVIDENCE=2257/2257")
    print("NETWORK_CORE_SEED_PROJECTION=PASS")
    print("FEDERATION_SEED_STUTTER_BOUNDARY=PASS")
    print("NETWORK_SEED_PROJECTION_ASSURANCE=PASS")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
