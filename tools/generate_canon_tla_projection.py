#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "extension/canonical/source/network-extension-model.json"
RELATION_PATH = ROOT / "extension/canonical/assurance/canon-tla-refinement.json"
OUTPUT_PATH = ROOT / "extension/canonical/formal/NetworkCanonProjection.tla"

EXPECTED_PROFILE = "ASET-NETWORK-CANON-TLA-PROJECTION-V2"
EXPECTED_VERSION = "0.1.0-alpha.2"
EXPECTED_STATUS = "FEDERATION_RECOGNITION_CORE_ALPHA2_FORMAL_FOUNDATION"
EXPECTED_TRANSITIONS = [
    "FEDERATION_GENESIS",
    "MEMBER_JOIN",
    "ROUTE_GRANT",
    "EXPORT_ARTIFACT",
    "OBSERVE_IMPORT",
    "RECORD_RECOGNITION",
    "SUSPEND_ROUTE",
    "MEMBER_WITHDRAW",
]
EXPECTED_INVARIANTS = [f"NET-INV-{index:03d}" for index in range(1, 13)]
EXPECTED_REQUIREMENTS = [f"NET-REQ-{index:03d}" for index in range(1, 9)]
EXPECTED_SEMANTIC_STATE_FIELDS = [
    "federation_id",
    "federation_epoch",
    "members",
    "routes",
    "exports",
    "imports",
    "recognitions",
]


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_inputs(model: dict[str, Any], relation: dict[str, Any]) -> None:
    errors: list[str] = []
    if model.get("document_type") != "aset-network-extension-model":
        errors.append("unsupported source document type")
    if model.get("extension_id") != "ASET-NETWORK-EXTENSION":
        errors.append("unsupported extension id")
    if model.get("version") != EXPECTED_VERSION:
        errors.append("unsupported extension version")
    if model.get("status") != EXPECTED_STATUS:
        errors.append("unsupported extension status")
    if model.get("transition_kinds") != EXPECTED_TRANSITIONS:
        errors.append("unsupported canonical transition catalogue")
    if [item.get("id") for item in model.get("invariants", [])] != EXPECTED_INVARIANTS:
        errors.append("unsupported invariant catalogue")
    if [item.get("id") for item in model.get("requirements", [])] != EXPECTED_REQUIREMENTS:
        errors.append("unsupported requirement catalogue")
    partition = model.get("state_partition", {})
    if partition.get("semantic_state_fields") != EXPECTED_SEMANTIC_STATE_FIELDS:
        errors.append("unsupported semantic-state partition")
    if partition.get("evidence_history_fields") != ["history"]:
        errors.append("unsupported evidence-history partition")

    generated = relation.get("generated_projection", {})
    if generated.get("profile") != EXPECTED_PROFILE:
        errors.append("unsupported canon-to-TLA projection profile")
    if generated.get("generator") != "tools/generate_canon_tla_projection.py":
        errors.append("projection generator binding mismatch")
    if generated.get("module") != "NetworkCanonProjection":
        errors.append("projection module binding mismatch")
    if generated.get("path") != "extension/canonical/formal/NetworkCanonProjection.tla":
        errors.append("projection path binding mismatch")
    if relation.get("relation_type") != (
        "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF"
    ):
        errors.append("projection relation type mismatch")
    source = relation.get("source_model", {})
    if source.get("path") != MODEL_PATH.relative_to(ROOT).as_posix():
        errors.append("projection source path mismatch")
    actual_source_sha = sha256_bytes(MODEL_PATH.read_bytes())
    if source.get("sha256") != actual_source_sha:
        errors.append("projection source digest mismatch")
    if source.get("version") != EXPECTED_VERSION:
        errors.append("projection source version mismatch")
    if relation.get("scope") != "DECLARED_CANONICAL_SAFETY_PROJECTION":
        errors.append("projection scope mismatch")

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))


def render(model: dict[str, Any], relation: dict[str, Any]) -> str:
    source_sha = sha256_bytes(canonical_json(model))
    profile = relation["generated_projection"]["profile"]
    return f'''---------------------- MODULE NetworkCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/network-extension-model.json
Source SHA-256: {source_sha}
Projection profile: {profile}

This is a standalone safety projection. It does not EXTEND or instantiate
NetworkExtension. NetworkCanonRefinementProofs.tla explicitly instantiates
this generated model onto the handwritten assurance state.

Evidence-history trace semantics and conditional liveness are separate
assurance surfaces and intentionally remain outside CanonSafetySpec.
The deterministic generator is part of the assurance trusted computing base.
***************************************************************************)

CONSTANTS Contexts, Artifacts

ASSUME /\\ Contexts # {{}}
       /\\ Artifacts # {{}}

CanonMemberStates == {{"ABSENT", "ACTIVE", "WITHDRAWN"}}

CanonExport(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
CanonExportUniverse ==
  [source : Contexts,
   target : Contexts,
   artifact : Artifacts]
CanonRouteUniverse == Contexts \\X Contexts

VARIABLES
  memberStatus,
  routes,
  activeRoutes,
  exports,
  inTransit,
  delivered,
  imports,
  accepted,
  denied,
  authorityOwner,
  superiorContexts

CanonVars == <<memberStatus, routes, activeRoutes, exports, inTransit, delivered,
               imports, accepted, denied, authorityOwner, superiorContexts>>

CanonInit ==
  /\\ memberStatus = [c \\in Contexts |-> "ABSENT"]
  /\\ routes = {{}}
  /\\ activeRoutes = {{}}
  /\\ exports = {{}}
  /\\ inTransit = {{}}
  /\\ delivered = {{}}
  /\\ imports = {{}}
  /\\ accepted = {{}}
  /\\ denied = {{}}
  /\\ authorityOwner = [c \\in Contexts |-> c]
  /\\ superiorContexts = {{}}

CanonJoin(c) ==
  /\\ c \\in Contexts
  /\\ memberStatus[c] = "ABSENT"
  /\\ memberStatus' = [memberStatus EXCEPT ![c] = "ACTIVE"]
  /\\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonGrantRoute(s, t) ==
  /\\ s \\in Contexts
  /\\ t \\in Contexts
  /\\ s # t
  /\\ memberStatus[s] = "ACTIVE"
  /\\ memberStatus[t] = "ACTIVE"
  /\\ <<s, t>> \\notin routes
  /\\ routes' = routes \\cup {{<<s, t>>}}
  /\\ activeRoutes' = activeRoutes \\cup {{<<s, t>>}}
  /\\ UNCHANGED <<memberStatus, exports, inTransit, delivered, imports,
                  accepted, denied, authorityOwner, superiorContexts>>

CanonExportArtifact(s, t, a) ==
  LET e == CanonExport(s, t, a)
  IN /\\ <<s, t>> \\in activeRoutes
     /\\ e \\notin exports
     /\\ exports' = exports \\cup {{e}}
     /\\ inTransit' = inTransit \\cup {{e}}
     /\\ UNCHANGED <<memberStatus, routes, activeRoutes, delivered, imports,
                     accepted, denied, authorityOwner, superiorContexts>>

CanonDeliver(e) ==
  /\\ e \\in inTransit
  /\\ e \\notin delivered
  /\\ delivered' = delivered \\cup {{e}}
  /\\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonObserve(e) ==
  /\\ e \\in delivered
  /\\ e \\notin imports
  /\\ memberStatus[e.target] = "ACTIVE"
  /\\ imports' = imports \\cup {{e}}
  /\\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, accepted, denied, authorityOwner,
                  superiorContexts>>

CanonResolveAccept(e) ==
  /\\ e \\in imports
  /\\ e \\notin accepted \\cup denied
  /\\ accepted' = accepted \\cup {{e}}
  /\\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, denied, authorityOwner, superiorContexts>>

CanonResolveDeny(e) ==
  /\\ e \\in imports
  /\\ e \\notin accepted \\cup denied
  /\\ denied' = denied \\cup {{e}}
  /\\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, accepted, authorityOwner,
                  superiorContexts>>

CanonResolve(e) == CanonResolveAccept(e) \\/ CanonResolveDeny(e)

CanonSuspendRoute(s, t) ==
  /\\ <<s, t>> \\in activeRoutes
  /\\ activeRoutes' = activeRoutes \\ {{<<s, t>>}}
  /\\ UNCHANGED <<memberStatus, routes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonWithdraw(c) ==
  /\\ c \\in Contexts
  /\\ memberStatus[c] = "ACTIVE"
  /\\ \\A r \\in activeRoutes : c \\notin {{r[1], r[2]}}
  /\\ memberStatus' = [memberStatus EXCEPT ![c] = "WITHDRAWN"]
  /\\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonNetworkAction ==
  \\/ \\E c \\in Contexts : CanonJoin(c)
  \\/ \\E s \\in Contexts, t \\in Contexts : CanonGrantRoute(s, t)
  \\/ \\E s \\in Contexts, t \\in Contexts, a \\in Artifacts :
       CanonExportArtifact(s, t, a)
  \\/ \\E e \\in CanonExportUniverse : CanonDeliver(e)
  \\/ \\E e \\in CanonExportUniverse : CanonObserve(e)
  \\/ \\E e \\in CanonExportUniverse : CanonResolve(e)
  \\/ \\E s \\in Contexts, t \\in Contexts : CanonSuspendRoute(s, t)
  \\/ \\E c \\in Contexts : CanonWithdraw(c)

CanonSafetySpec == CanonInit /\\ [][CanonNetworkAction]_CanonVars

CanonSafetyTerminal ==
  \\A c \\in Contexts : memberStatus[c] = "WITHDRAWN"

CanonNoUnexpectedSafetyDeadlock ==
  CanonSafetyTerminal \\/ ENABLED CanonNetworkAction

CanonTypeOK ==
  /\\ memberStatus \\in [Contexts -> CanonMemberStates]
  /\\ routes \\subseteq CanonRouteUniverse
  /\\ activeRoutes \\subseteq routes
  /\\ exports \\subseteq CanonExportUniverse
  /\\ inTransit \\subseteq exports
  /\\ delivered \\subseteq exports
  /\\ imports \\subseteq delivered
  /\\ accepted \\subseteq imports
  /\\ denied \\subseteq imports
  /\\ authorityOwner \\in [Contexts -> Contexts]
  /\\ superiorContexts \\subseteq Contexts

CanonNoSelfRoute ==
  \\A r \\in routes : r[1] # r[2]

CanonActiveRouteMembersActive ==
  \\A r \\in activeRoutes :
    /\\ memberStatus[r[1]] = "ACTIVE"
    /\\ memberStatus[r[2]] = "ACTIVE"

CanonExportBindingPreserved ==
  \\A e \\in exports :
    /\\ <<e.source, e.target>> \\in routes
    /\\ e.source # e.target

CanonImportRequiresDelivery == imports \\subseteq delivered
CanonRecognitionRequiresImport == accepted \\cup denied \\subseteq imports
CanonTerminalRecognitionDisjoint == accepted \\cap denied = {{}}

CanonLocalAuthoritySovereignty ==
  \\A c \\in Contexts : authorityOwner[c] = c

CanonNoImplicitSuperContext == superiorContexts = {{}}

CanonContextImports(c) == {{e \\in imports : e.target = c}}
CanonContextAccepted(c) == {{e \\in accepted : e.target = c}}
CanonContextDenied(c) == {{e \\in denied : e.target = c}}

CanonPerContextSeedProjectionWellFormed ==
  \\A c \\in Contexts :
    /\\ CanonContextAccepted(c) \\subseteq CanonContextImports(c)
    /\\ CanonContextDenied(c) \\subseteq CanonContextImports(c)
    /\\ CanonContextAccepted(c) \\cap CanonContextDenied(c) = {{}}

CanonNetworkDoesNotWeakenSeedBoundary ==
  /\\ CanonRecognitionRequiresImport
  /\\ CanonTerminalRecognitionDisjoint
  /\\ CanonLocalAuthoritySovereignty
  /\\ CanonNoImplicitSuperContext
  /\\ CanonPerContextSeedProjectionWellFormed

=============================================================================
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    relation = json.loads(RELATION_PATH.read_text(encoding="utf-8"))
    validate_inputs(model, relation)
    rendered = render(model, relation).encode("utf-8")

    if args.check:
        if not OUTPUT_PATH.is_file():
            print("NETWORK_CANON_PROJECTION_CHECK=FAIL")
            print(f"NETWORK_CANON_PROJECTION_ERROR=missing {OUTPUT_PATH.relative_to(ROOT)}")
            return 1
        actual = OUTPUT_PATH.read_bytes()
        if actual != rendered:
            print("NETWORK_CANON_PROJECTION_CHECK=FAIL")
            print("NETWORK_CANON_PROJECTION_ERROR=committed projection is stale")
            print(f"NETWORK_CANON_PROJECTION_EXPECTED_SHA256={sha256_bytes(rendered)}")
            print(f"NETWORK_CANON_PROJECTION_ACTUAL_SHA256={sha256_bytes(actual)}")
            return 1
        print(f"NETWORK_CANON_PROJECTION={OUTPUT_PATH.relative_to(ROOT)}")
        print(f"NETWORK_CANON_PROJECTION_SHA256={sha256_bytes(actual)}")
        print("NETWORK_CANON_PROJECTION_CHECK=PASS")
        return 0

    OUTPUT_PATH.write_bytes(rendered)
    print(f"NETWORK_CANON_PROJECTION={OUTPUT_PATH.relative_to(ROOT)}")
    print(f"NETWORK_CANON_PROJECTION_SHA256={sha256_bytes(rendered)}")
    print("NETWORK_CANON_PROJECTION_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
