from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "extension/canonical"
F = C / "formal"
MODEL = C / "source/network-extension-model.json"
BIND = ROOT / "upstream/ASET_SEED_BINDING.json"
REL = F / "canon-tla-relation.json"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    binding = json.loads(BIND.read_text())
    canon_evidence = json.loads((C / "assurance/canon-refinement-proof.json").read_text())
    seed_evidence = json.loads((C / "assurance/seed-refinement-proof.json").read_text())
    relation = {
        "document_type": "aset-network-canon-tla-relation",
        "schema_version": 1,
        "profile": "ASET-NETWORK-CANON-TLA-PROJECTION-V3",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "source_model": {
            "path": MODEL.relative_to(ROOT).as_posix(),
            "sha256": sha(MODEL),
            "version": "0.1.0-alpha.3",
        },
        "target_model": {
            "module": "NetworkExtension",
            "path": "extension/canonical/formal/NetworkExtension.tla",
            "sha256": sha(F / "NetworkExtension.tla"),
            "scope": "MINIMAL_ADMISSION_SEMANTIC_STATE_SAFETY_MODEL",
        },
        "canon_projection": {
            "profile": "ASET-NETWORK-CANON-TLA-PROJECTION-V3",
            "generator": "tools/generate_canon_tla_projection.py",
            "module": "NetworkCanonProjection",
            "path": "extension/canonical/formal/NetworkCanonProjection.tla",
            "sha256": sha(F / "NetworkCanonProjection.tla"),
            "proof_module": "NetworkCanonRefinementProofs",
            "proof_path": "extension/canonical/formal/NetworkCanonRefinementProofs.tla",
            "proof_sha256": sha(F / "NetworkCanonRefinementProofs.tla"),
            "final_theorems": canon_evidence["proof_gate"]["final_theorems"],
            "obligations_proved": canon_evidence["proof_gate"]["obligations_proved"],
            "status": canon_evidence["status"],
        },
        "projection_surfaces": {
            "semantic_state": {
                "canon_selector": "/state_partition/semantic_state_fields",
                "formal_model": "NetworkExtension",
                "scope": "MINIMAL_ADMISSION_SAFETY_AND_SEED_PROJECTION",
            },
            "evidence_history": {
                "canon_selector": "/state_partition/evidence_history_fields",
                "formal_model": "NetworkHistory",
                "scope": "APPEND_ONLY_ADMISSION_TRACE",
            },
            "federation_lifecycle": {
                "owner": "ASET-NETWORK-FEDERATION-PROFILE-V1",
                "required_for_core_conformance": False,
                "formal_model": "FederationProfile",
            },
            "terminal_recognition": {"owner": "PINNED_TARGET_LOCAL_SEED"},
        },
        "seed_projection": {
            "module": "NetworkExtensionSeedProjection",
            "path": "extension/canonical/formal/NetworkExtensionSeedProjection.tla",
            "sha256": sha(F / "NetworkExtensionSeedProjection.tla"),
            "contract": "PerContextSeedProjectionContract",
        },
        "seed_refinement": {
            "mapping_module": "NetworkExtensionSeedRefinement",
            "mapping_path": "extension/canonical/formal/NetworkExtensionSeedRefinement.tla",
            "mapping_sha256": sha(F / "NetworkExtensionSeedRefinement.tla"),
            "proof_module": "NetworkExtensionSeedRefinementProofs",
            "proof_path": "extension/canonical/formal/NetworkExtensionSeedRefinementProofs.tla",
            "proof_sha256": sha(F / "NetworkExtensionSeedRefinementProofs.tla"),
            "upstream_module": "SeedResolution",
            "upstream_sha256": (
                "sha256:1c0ebb27ed52da289f0981dcb11b61b6"
                "a7fc5c4a030ba434ae0b1d53b286b926"
            ),
            "mapping": {
                "resolution_ids": "ObservationUniverse",
                "bindings": "target-scoped Contexts x Artifacts",
                "authorities": "target Contexts",
                "requests": "imports",
                "terminal_meta": "EMPTY_NETWORK_OWNERSHIP",
                "conflicts": "EMPTY_IN_NETWORK_PROJECTION",
            },
            "admit_import": "SeedResolution.RegisterRequest",
            "terminal_recognition": "OUTSIDE_NETWORK_OWNERSHIP",
            "obligations_proved": seed_evidence["proof_gate"]["obligations_proved"],
            "status": seed_evidence["status"],
        },
        "safety_model": {
            "specification": "SafetySpec",
            "config": "extension/canonical/formal/NetworkExtension.cfg",
            "sha256": sha(F / "NetworkExtension.cfg"),
        },
        "tlc_harness": {
            "module": "NetworkExtensionTLC",
            "path": "extension/canonical/formal/NetworkExtensionTLC.tla",
            "sha256": sha(F / "NetworkExtensionTLC.tla"),
            "config": "extension/canonical/formal/NetworkExtensionTLC.cfg",
            "config_sha256": sha(F / "NetworkExtensionTLC.cfg"),
            "scope": "BOUNDED_TEMPORAL_MODEL_CHECKING_ONLY",
            "properties": ["ImportsAppendOnlyTemporal"],
        },
        "history_model": {
            "module": "NetworkHistory",
            "path": "extension/canonical/formal/NetworkHistory.tla",
            "sha256": sha(F / "NetworkHistory.tla"),
            "config": "extension/canonical/formal/NetworkHistory.cfg",
            "config_sha256": sha(F / "NetworkHistory.cfg"),
            "scope": "APPEND_ONLY_ADMISSION_TRACE",
        },
        "federation_assurance": {
            "safety_model": {
                "module": "FederationProfile",
                "path": "extension/canonical/formal/FederationProfile.tla",
                "sha256": sha(F / "FederationProfile.tla"),
                "config": "extension/canonical/formal/FederationProfile.cfg",
                "config_sha256": sha(F / "FederationProfile.cfg"),
                "scope": "OPTIONAL_PROFILE_SAFETY",
            },
            "liveness_model": {
                "module": "FederationCompositionLiveness",
                "path": "extension/canonical/formal/FederationCompositionLiveness.tla",
                "sha256": sha(F / "FederationCompositionLiveness.tla"),
                "config": "extension/canonical/formal/FederationCompositionLiveness.cfg",
                "config_sha256": sha(F / "FederationCompositionLiveness.cfg"),
                "scope": "OPTIONAL_COMPOSITION_LIVENESS_ASSURANCE",
                "seed_resolution_owner": "PINNED_TARGET_LOCAL_SEED",
            },
        },
        "upstream_seed": {
            "release_tag": binding["seed_release_tag"],
            "release_commit": binding["seed_release_commit"],
            "canon_id": binding["canon_id"],
            "canon_version": binding["canon_version"],
            "canon_package_digest": binding["canon_package_digest"],
            "compatibility_standard": binding["compatibility_standard"],
            "compatibility_standard_profile": binding["compatibility_standard_profile"],
            "conformance_kit_sha256": binding["seed_conformance_kit_sha256"],
        },
        "invariant_coverage": [
            {"id": "NET-INV-001", "tla": "NoRemoteAuthorityState", "status": "TLC_INVARIANT"},
            {"id": "NET-INV-002", "tla": "AdmissionFailClosed", "status": "TLC_INVARIANT"},
            {"id": "NET-INV-003", "tla": "NoTerminalRecognitionState", "status": "TLC_INVARIANT"},
            {"id": "NET-INV-004", "tla": "NetworkHistory", "status": "TLC_TRACE_PROPERTY"},
            {
                "id": "NET-INV-005",
                "tla": "set membership guard + reference conformance",
                "status": "STATE_AND_CONFORMANCE",
            },
            {
                "id": "NET-INV-006",
                "tla": "NetworkDoesNotWeakenSeedBoundary + Seed refinement",
                "status": "TLC_PLUS_TLAPS_PROVED",
            },
        ],
        "operation_coverage": [{"kind": "ADMIT_IMPORT", "tla_action": "AdmitImport"}],
        "excluded_claims": [
            "wire-schema equivalence",
            "cryptographic security",
            "transport availability",
            "federation lifecycle as core semantics",
            "terminal recognition as Network state",
            "obligation counts as normative semantics",
        ],
    }
    relation["relation_digest"] = "sha256:" + hashlib.sha256(canonical_bytes(relation)).hexdigest()
    REL.write_bytes(canonical_bytes(relation))
    print(f"FORMAL_RELATION={REL.relative_to(ROOT)}")
    print(f"FORMAL_RELATION_DIGEST={relation['relation_digest']}")
    print("FORMAL_RELATION_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
