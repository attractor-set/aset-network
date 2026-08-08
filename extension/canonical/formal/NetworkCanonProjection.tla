---------------------- MODULE NetworkCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/network-extension-model.json
Source SHA-256: sha256:ce8ae7650a0d17dc0a2bee01428793ea5e204be34360d6d58b07a2b0377ba24c
Projection profile: ASET-NETWORK-CANON-TLA-PROJECTION-V2

This is a standalone safety projection. It does not EXTEND or instantiate
NetworkExtension. NetworkCanonRefinementProofs.tla explicitly instantiates
this generated model onto the handwritten assurance state.

Evidence-history trace semantics and conditional liveness are separate
assurance surfaces and intentionally remain outside CanonSafetySpec.
The deterministic generator is part of the assurance trusted computing base.
***************************************************************************)

CONSTANTS Contexts, Artifacts

ASSUME /\ Contexts # {}
       /\ Artifacts # {}

CanonMemberStates == {"ABSENT", "ACTIVE", "WITHDRAWN"}

CanonExport(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
CanonExportUniverse ==
  [source : Contexts,
   target : Contexts,
   artifact : Artifacts]
CanonRouteUniverse == Contexts \X Contexts

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
  /\ memberStatus = [c \in Contexts |-> "ABSENT"]
  /\ routes = {}
  /\ activeRoutes = {}
  /\ exports = {}
  /\ inTransit = {}
  /\ delivered = {}
  /\ imports = {}
  /\ accepted = {}
  /\ denied = {}
  /\ authorityOwner = [c \in Contexts |-> c]
  /\ superiorContexts = {}

CanonJoin(c) ==
  /\ c \in Contexts
  /\ memberStatus[c] = "ABSENT"
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "ACTIVE"]
  /\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonGrantRoute(s, t) ==
  /\ s \in Contexts
  /\ t \in Contexts
  /\ s # t
  /\ memberStatus[s] = "ACTIVE"
  /\ memberStatus[t] = "ACTIVE"
  /\ <<s, t>> \notin routes
  /\ routes' = routes \cup {<<s, t>>}
  /\ activeRoutes' = activeRoutes \cup {<<s, t>>}
  /\ UNCHANGED <<memberStatus, exports, inTransit, delivered, imports,
                  accepted, denied, authorityOwner, superiorContexts>>

CanonExportArtifact(s, t, a) ==
  LET e == CanonExport(s, t, a)
  IN /\ <<s, t>> \in activeRoutes
     /\ e \notin exports
     /\ exports' = exports \cup {e}
     /\ inTransit' = inTransit \cup {e}
     /\ UNCHANGED <<memberStatus, routes, activeRoutes, delivered, imports,
                     accepted, denied, authorityOwner, superiorContexts>>

CanonDeliver(e) ==
  /\ e \in inTransit
  /\ e \notin delivered
  /\ delivered' = delivered \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonObserve(e) ==
  /\ e \in delivered
  /\ e \notin imports
  /\ memberStatus[e.target] = "ACTIVE"
  /\ imports' = imports \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, accepted, denied, authorityOwner,
                  superiorContexts>>

CanonResolveAccept(e) ==
  /\ e \in imports
  /\ e \notin accepted \cup denied
  /\ accepted' = accepted \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, denied, authorityOwner, superiorContexts>>

CanonResolveDeny(e) ==
  /\ e \in imports
  /\ e \notin accepted \cup denied
  /\ denied' = denied \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, accepted, authorityOwner,
                  superiorContexts>>

CanonResolve(e) == CanonResolveAccept(e) \/ CanonResolveDeny(e)

CanonSuspendRoute(s, t) ==
  /\ <<s, t>> \in activeRoutes
  /\ activeRoutes' = activeRoutes \ {<<s, t>>}
  /\ UNCHANGED <<memberStatus, routes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonWithdraw(c) ==
  /\ c \in Contexts
  /\ memberStatus[c] = "ACTIVE"
  /\ \A r \in activeRoutes : c \notin {r[1], r[2]}
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "WITHDRAWN"]
  /\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

CanonNetworkAction ==
  \/ \E c \in Contexts : CanonJoin(c)
  \/ \E s \in Contexts, t \in Contexts : CanonGrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts :
       CanonExportArtifact(s, t, a)
  \/ \E e \in CanonExportUniverse : CanonDeliver(e)
  \/ \E e \in CanonExportUniverse : CanonObserve(e)
  \/ \E e \in CanonExportUniverse : CanonResolve(e)
  \/ \E s \in Contexts, t \in Contexts : CanonSuspendRoute(s, t)
  \/ \E c \in Contexts : CanonWithdraw(c)

CanonSafetySpec == CanonInit /\ [][CanonNetworkAction]_CanonVars

CanonSafetyTerminal ==
  \A c \in Contexts : memberStatus[c] = "WITHDRAWN"

CanonNoUnexpectedSafetyDeadlock ==
  CanonSafetyTerminal \/ ENABLED CanonNetworkAction

CanonTypeOK ==
  /\ memberStatus \in [Contexts -> CanonMemberStates]
  /\ routes \subseteq CanonRouteUniverse
  /\ activeRoutes \subseteq routes
  /\ exports \subseteq CanonExportUniverse
  /\ inTransit \subseteq exports
  /\ delivered \subseteq exports
  /\ imports \subseteq delivered
  /\ accepted \subseteq imports
  /\ denied \subseteq imports
  /\ authorityOwner \in [Contexts -> Contexts]
  /\ superiorContexts \subseteq Contexts

CanonNoSelfRoute ==
  \A r \in routes : r[1] # r[2]

CanonActiveRouteMembersActive ==
  \A r \in activeRoutes :
    /\ memberStatus[r[1]] = "ACTIVE"
    /\ memberStatus[r[2]] = "ACTIVE"

CanonExportBindingPreserved ==
  \A e \in exports :
    /\ <<e.source, e.target>> \in routes
    /\ e.source # e.target

CanonImportRequiresDelivery == imports \subseteq delivered
CanonRecognitionRequiresImport == accepted \cup denied \subseteq imports
CanonTerminalRecognitionDisjoint == accepted \cap denied = {}

CanonLocalAuthoritySovereignty ==
  \A c \in Contexts : authorityOwner[c] = c

CanonNoImplicitSuperContext == superiorContexts = {}

CanonContextImports(c) == {e \in imports : e.target = c}
CanonContextAccepted(c) == {e \in accepted : e.target = c}
CanonContextDenied(c) == {e \in denied : e.target = c}

CanonPerContextSeedProjectionWellFormed ==
  \A c \in Contexts :
    /\ CanonContextAccepted(c) \subseteq CanonContextImports(c)
    /\ CanonContextDenied(c) \subseteq CanonContextImports(c)
    /\ CanonContextAccepted(c) \cap CanonContextDenied(c) = {}

CanonNetworkDoesNotWeakenSeedBoundary ==
  /\ CanonRecognitionRequiresImport
  /\ CanonTerminalRecognitionDisjoint
  /\ CanonLocalAuthoritySovereignty
  /\ CanonNoImplicitSuperContext
  /\ CanonPerContextSeedProjectionWellFormed

=============================================================================
