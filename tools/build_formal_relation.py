from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "extension/canonical/source/network-extension-model.json"
FORMAL = ROOT / "extension/canonical/formal"
RELATION = FORMAL / "canon-tla-relation.json"
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"
LIVENESS = ROOT / "extension/canonical/liveness/liveness-profile.json"
PROOF_EVIDENCE = ROOT / "extension/canonical/assurance/seed-refinement-proof.json"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    proof_evidence = json.loads(PROOF_EVIDENCE.read_text(encoding="utf-8"))
    relation = {
        "document_type": "aset-network-canon-tla-relation",
        "schema_version": 1,
        "profile": "ASET-NETWORK-CANON-TLA-PROJECTION-V1",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "source_model": {
            "path": MODEL.relative_to(ROOT).as_posix(),
            "sha256": sha(MODEL),
        },
        "target_model": {
            "module": "NetworkExtension",
            "path": (FORMAL / "NetworkExtension.tla").relative_to(ROOT).as_posix(),
            "sha256": sha(FORMAL / "NetworkExtension.tla"),
            "scope": "SEMANTIC_STATE_SAFETY_AND_PROGRESS",
        },
        "projection_surfaces": {
            "semantic_state": {
                "canon_selector": "/state_partition/semantic_state_fields",
                "formal_model": "NetworkExtension",
                "scope": "SAFETY_AND_SEED_PROJECTION",
            },
            "evidence_history": {
                "canon_selector": "/state_partition/evidence_history_fields",
                "formal_model": "NetworkHistory",
                "scope": "NET-INV-010_TRACE_PROJECTION",
            },
            "conditional_liveness": {
                "canon_selector": "extension/canonical/liveness/liveness-profile.json",
                "formal_model": "NetworkExtension.FairSpec",
                "scope": "ASET-NETWORK-LIVENESS-V1",
            },
        },
        "seed_projection": {
            "module": "NetworkExtensionSeedProjection",
            "path": (FORMAL / "NetworkExtensionSeedProjection.tla").relative_to(ROOT).as_posix(),
            "sha256": sha(FORMAL / "NetworkExtensionSeedProjection.tla"),
            "contract": "PerContextSeedProjectionContract",
            "exact_seed_tlaps_refinement": "MECHANICALLY_PROVED",
        },
        "seed_refinement": {
            "mapping_module": "NetworkExtensionSeedRefinement",
            "mapping_path": (
                FORMAL / "NetworkExtensionSeedRefinement.tla"
            ).relative_to(ROOT).as_posix(),
            "mapping_sha256": sha(FORMAL / "NetworkExtensionSeedRefinement.tla"),
            "proof_module": "NetworkExtensionSeedRefinementProofs",
            "proof_path": (
                FORMAL / "NetworkExtensionSeedRefinementProofs.tla"
            ).relative_to(ROOT).as_posix(),
            "proof_sha256": sha(FORMAL / "NetworkExtensionSeedRefinementProofs.tla"),
            "upstream_module": "SeedResolution",
            "upstream_path": "seed/canonical/formal/SeedResolution.tla",
            "upstream_sha256": (
                "sha256:1c0ebb27ed52da289f0981dcb11b61b6"
                "a7fc5c4a030ba434ae0b1d53b286b926"
            ),
            "upstream_materialization": "EXTERNAL_PINNED_SEED_SOURCE_NOT_VENDORED",
            "mapping": {
                "resolution_ids": "ExportUniverse",
                "bindings": "target-scoped Contexts x Artifacts",
                "authorities": "Contexts",
                "requests": "imports",
                "allow_terminals": "accepted",
                "block_terminals": "denied",
                "conflicts": "EMPTY_IN_NETWORK_PROJECTION",
            },
            "network_only_actions": "SEED_STUTTER",
            "observe_import": "SeedResolution.RegisterRequest",
            "resolve_accept": "SeedResolution.SubmitResolution(ALLOW)",
            "resolve_deny": "SeedResolution.SubmitResolution(BLOCK)",
            "final_theorems": proof_evidence["proof_gate"]["final_theorems"],
            "proof_evidence_path": PROOF_EVIDENCE.relative_to(ROOT).as_posix(),
            "proof_evidence_sha256": sha(PROOF_EVIDENCE),
            "tlapm_commit": proof_evidence["tlapm"]["commit"],
            "tlapm_version": proof_evidence["tlapm"]["version"],
            "obligations_proved": proof_evidence["proof_gate"]["obligations_proved"],
            "obligation_count_semantics": proof_evidence["proof_gate"][
                "obligation_count_semantics"
            ],
            "status": proof_evidence["status"],
        },
        "safety_model": {
            "specification": "SafetySpec",
            "config": (FORMAL / "NetworkExtension.cfg").relative_to(ROOT).as_posix(),
            "sha256": sha(FORMAL / "NetworkExtension.cfg"),
        },
        "history_model": {
            "module": "NetworkHistory",
            "path": (FORMAL / "NetworkHistory.tla").relative_to(ROOT).as_posix(),
            "sha256": sha(FORMAL / "NetworkHistory.tla"),
            "specification": "HistorySpec",
            "config": (FORMAL / "NetworkHistory.cfg").relative_to(ROOT).as_posix(),
            "config_sha256": sha(FORMAL / "NetworkHistory.cfg"),
            "scope": "NET-INV-010_TRACE_PROJECTION",
            "properties": [
                "HistoryPrefixPreserved",
                "AcceptedTransitionAppendsExactlyOne",
            ],
        },
        "liveness_model": {
            "profile": "ASET-NETWORK-LIVENESS-V1",
            "profile_path": LIVENESS.relative_to(ROOT).as_posix(),
            "profile_sha256": sha(LIVENESS),
            "specification": "FairSpec",
            "config": (FORMAL / "NetworkExtensionLiveness.cfg").relative_to(ROOT).as_posix(),
            "config_sha256": sha(FORMAL / "NetworkExtensionLiveness.cfg"),
            "required_for_core_conformance": False,
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
            "seed_canon_tla_projection_profile": "ASET-SEED-CANON-TLA-PROJECTION-V5",
        },
        "invariant_coverage": [
            {"id": "NET-INV-001", "tla": "LocalAuthoritySovereignty", "status": "TLC_INVARIANT"},
            {
                "id": "NET-INV-002",
                "tla": "ExportArtifact action frame conditions",
                "status": "TLC_ACTION_ABSTRACTION",
            },
            {
                "id": "NET-INV-003",
                "tla": "ProjectedStatus / ProjectedEnforcement",
                "status": "TLC_PROJECTION_INVARIANT",
            },
            {
                "id": "NET-INV-004",
                "tla": "RecognitionRequiresImport / TerminalRecognitionDisjoint",
                "status": "TLC_INVARIANT",
            },
            {
                "id": "NET-INV-005",
                "tla": "ProjectionFailClosed / ProjectionAllowRequiresLocalAccept",
                "status": "TLC_PROJECTION_INVARIANT",
            },
            {"id": "NET-INV-006", "tla": "ExportBindingPreserved", "status": "TLC_INVARIANT"},
            {
                "id": "NET-INV-007",
                "tla": "ActiveRouteMembersActive / NoSelfRoute",
                "status": "TLC_INVARIANT",
            },
            {"id": "NET-INV-008", "tla": "Withdraw guard", "status": "TLC_ACTION_ABSTRACTION"},
            {"id": "NET-INV-009", "tla": "NoImplicitSuperContext", "status": "TLC_INVARIANT"},
            {
                "id": "NET-INV-010",
                "tla": (
                    "NetworkHistory.HistoryPrefixPreserved / "
                    "AcceptedTransitionAppendsExactlyOne"
                ),
                "status": "TLC_TRACE_PROPERTY",
            },
            {
                "id": "NET-INV-011",
                "tla": "set membership guards plus stuttering",
                "status": "TLC_STATE_ABSTRACTION",
            },
            {
                "id": "NET-INV-012",
                "tla": "NetworkDoesNotWeakenSeedBoundary",
                "status": "TLC_PROJECTION_INVARIANT",
            },
        ],
        "operation_coverage": [
            {"kind": "MEMBER_JOIN", "tla_action": "Join"},
            {"kind": "ROUTE_GRANT", "tla_action": "GrantRoute"},
            {"kind": "EXPORT_ARTIFACT", "tla_action": "ExportArtifact"},
            {"kind": "OBSERVE_IMPORT", "tla_action": "Observe"},
            {"kind": "RECORD_RECOGNITION", "tla_action": "ResolveAccept / ResolveDeny"},
            {"kind": "SUSPEND_ROUTE", "tla_action": "SuspendRoute"},
            {"kind": "MEMBER_WITHDRAW", "tla_action": "Withdraw"},
            {"kind": "FEDERATION_GENESIS", "tla_action": "Init", "status": "ABSTRACTED_IN_INIT"},
        ],
        "liveness_coverage": [
            {
                "id": "NET-LIVE-G-001",
                "tla": "EventuallyDelivered",
                "status": "TLC_LIVENESS_PROPERTY",
            },
            {
                "id": "NET-LIVE-G-002",
                "tla": "EventuallyObserved",
                "status": "TLC_LIVENESS_PROPERTY",
            },
            {
                "id": "NET-LIVE-G-003",
                "tla": "EventuallyResolved",
                "status": "TLC_LIVENESS_PROPERTY",
            },
        ],
        "excluded_claims": [
            "unbounded state-space proof",
            "wire-schema equivalence",
            "cryptographic security",
            "unconditional transport availability",
            "global agreement or eventual ACCEPT",
            "concrete Authority-ID and Binding construction beyond the declared "
            "refinement abstraction mapping",
        ],
    }
    relation["relation_digest"] = "sha256:" + hashlib.sha256(canonical_bytes(relation)).hexdigest()
    RELATION.write_bytes(canonical_bytes(relation))
    print(f"FORMAL_RELATION={RELATION.relative_to(ROOT)}")
    print(f"FORMAL_RELATION_DIGEST={relation['relation_digest']}")
    print("FORMAL_RELATION_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
