-------------------------- MODULE NetworkLegacyAlpha2 --------------------------
EXTENDS FiniteSets

(***************************************************************************
Formal assurance projection for ASET Network Extension 0.1.0-alpha.2.

The machine-readable model under extension/canonical/source is normative.
This TLA+ module is an assurance projection: it models the sovereignty,
routing, export/import, local recognition and conditional-progress boundary.
Transport is represented only as nondeterministic delivery state.

Execution history is intentionally excluded from this state vector.  The
append-only history obligation is checked in the separate bounded
NetworkHistory module so different execution permutations that reach the same
network semantic state can collapse to one TLC state.

Three assurance-state fields are intentionally easy to misread:
  * inTransit is monotonic retention of the fact that transport was initiated;
    it is not a queue of exports that are still pending delivery.
  * authorityOwner is a sovereignty witness fixed to Context-local ownership;
    it is not a mutable cross-context Authority registry.
  * superiorContexts is a sentinel kept empty so absence of an implicit
    super-context is explicit and machine-checkable.  It is not a placeholder
    for a planned federation-wide Authority hierarchy.
***************************************************************************)

CONSTANTS Contexts, Artifacts

ASSUME /\ Contexts # {}
       /\ Artifacts # {}

MemberStates == {"ABSENT", "ACTIVE", "WITHDRAWN"}

Export(s, t, a) == [source |-> s, target |-> t, artifact |-> a]

(*
Proof-friendly extensional form of the export universe.  It denotes exactly
the same records as {Export(s, t, a) : s \in Contexts, t \in Contexts,
a \in Artifacts}, while exposing record-field typing directly to TLAPS.
*)
ExportUniverse ==
  [source : Contexts,
   target : Contexts,
   artifact : Artifacts]
RouteUniverse == Contexts \X Contexts

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

vars == <<memberStatus, routes, activeRoutes, exports, inTransit, delivered,
          imports, accepted, denied, authorityOwner, superiorContexts>>

Init ==
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

Join(c) ==
  /\ c \in Contexts
  /\ memberStatus[c] = "ABSENT"
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "ACTIVE"]
  /\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

GrantRoute(s, t) ==
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

ExportArtifact(s, t, a) ==
  LET e == Export(s, t, a)
  IN /\ <<s, t>> \in activeRoutes
     /\ e \notin exports
     /\ exports' = exports \cup {e}
     /\ inTransit' = inTransit \cup {e}
     /\ UNCHANGED <<memberStatus, routes, activeRoutes, delivered, imports,
                     accepted, denied, authorityOwner, superiorContexts>>

(***************************************************************************
Deliver is an environment/transport action. It cannot alter target-local
Authority or recognition.  Delivery intentionally does not remove an export
from inTransit: inTransit records that transport was initiated, while
delivered records successful delivery.  This monotonic retention is an
assurance abstraction, not transient transport storage or a runtime queue.
Keeping the export retained also makes duplicate delivery representable as
idempotent stuttering after the first delivery.
***************************************************************************)
Deliver(e) ==
  /\ e \in inTransit
  /\ e \notin delivered
  /\ delivered' = delivered \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

Observe(e) ==
  /\ e \in delivered
  /\ e \notin imports
  /\ memberStatus[e.target] = "ACTIVE"
  /\ imports' = imports \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, accepted, denied, authorityOwner,
                  superiorContexts>>

ResolveAccept(e) ==
  /\ e \in imports
  /\ e \notin accepted \cup denied
  /\ accepted' = accepted \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, denied, authorityOwner, superiorContexts>>

ResolveDeny(e) ==
  /\ e \in imports
  /\ e \notin accepted \cup denied
  /\ denied' = denied \cup {e}
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports, inTransit,
                  delivered, imports, accepted, authorityOwner,
                  superiorContexts>>

Resolve(e) == ResolveAccept(e) \/ ResolveDeny(e)

SuspendRoute(s, t) ==
  /\ <<s, t>> \in activeRoutes
  /\ activeRoutes' = activeRoutes \ {<<s, t>>}
  /\ UNCHANGED <<memberStatus, routes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

Withdraw(c) ==
  /\ c \in Contexts
  /\ memberStatus[c] = "ACTIVE"
  /\ \A r \in activeRoutes : c \notin {r[1], r[2]}
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "WITHDRAWN"]
  /\ UNCHANGED <<routes, activeRoutes, exports, inTransit, delivered,
                  imports, accepted, denied, authorityOwner, superiorContexts>>

NetworkAction ==
  \/ \E c \in Contexts : Join(c)
  \/ \E s \in Contexts, t \in Contexts : GrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ExportArtifact(s, t, a)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E e \in ExportUniverse : Observe(e)
  \/ \E e \in ExportUniverse : Resolve(e)
  \/ \E s \in Contexts, t \in Contexts : SuspendRoute(s, t)
  \/ \E c \in Contexts : Withdraw(c)

(***************************************************************************
ProgressAction excludes withdrawal. This is the finite TLC realization of
NET-LIVE-A-004: a target whose progress is claimed is not permanently removed
by the environment. SafetySpec itself permits withdrawal.
***************************************************************************)
ProgressAction ==
  \/ \E c \in Contexts : Join(c)
  \/ \E s \in Contexts, t \in Contexts : GrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ExportArtifact(s, t, a)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E e \in ExportUniverse : Observe(e)
  \/ \E e \in ExportUniverse : Resolve(e)
  \/ \E s \in Contexts, t \in Contexts : SuspendRoute(s, t)

SafetySpec == Init /\ [][NetworkAction]_vars

(***************************************************************************
TLC reports a syntactic deadlock when NetworkAction has no enabled successor.
For SafetySpec, the all-WITHDRAWN state is an intentional terminal/quiescent
state, not a safety violation.  The configs therefore disable TLC's generic
deadlock error and check the stronger model-specific predicate below instead.
***************************************************************************)
SafetyTerminal ==
  \A c \in Contexts : memberStatus[c] = "WITHDRAWN"

NoUnexpectedSafetyDeadlock ==
  SafetyTerminal \/ ENABLED NetworkAction

PendingProgress ==
  {e \in exports : e \notin delivered}
    \cup {e \in delivered : e \notin imports}
    \cup {e \in imports : e \notin accepted \cup denied}

NoPendingProgressDeadlock ==
  PendingProgress = {} \/ ENABLED ProgressAction

FairSpec ==
  /\ Init
  /\ [][ProgressAction]_vars
  /\ \A e \in ExportUniverse : WF_vars(Deliver(e))
  /\ \A e \in ExportUniverse : WF_vars(Observe(e))
  /\ \A e \in ExportUniverse : WF_vars(Resolve(e))

TypeOK ==
  /\ memberStatus \in [Contexts -> MemberStates]
  /\ routes \subseteq RouteUniverse
  /\ activeRoutes \subseteq routes
  /\ exports \subseteq ExportUniverse
  /\ inTransit \subseteq exports
  /\ delivered \subseteq exports
  /\ imports \subseteq delivered
  /\ accepted \subseteq imports
  /\ denied \subseteq imports
  /\ authorityOwner \in [Contexts -> Contexts]
  /\ superiorContexts \subseteq Contexts

NoSelfRoute ==
  \A r \in routes : r[1] # r[2]

ActiveRouteMembersActive ==
  \A r \in activeRoutes :
    /\ memberStatus[r[1]] = "ACTIVE"
    /\ memberStatus[r[2]] = "ACTIVE"

ExportBindingPreserved ==
  \A e \in exports :
    /\ <<e.source, e.target>> \in routes
    /\ e.source # e.target

ImportRequiresDelivery == imports \subseteq delivered

RecognitionRequiresImport == accepted \cup denied \subseteq imports

TerminalRecognitionDisjoint == accepted \cap denied = {}

LocalAuthoritySovereignty ==
  \A c \in Contexts : authorityOwner[c] = c

NoImplicitSuperContext == superiorContexts = {}

ContextImports(c) == {e \in imports : e.target = c}
ContextAccepted(c) == {e \in accepted : e.target = c}
ContextDenied(c) == {e \in denied : e.target = c}

PerContextSeedProjectionWellFormed ==
  \A c \in Contexts :
    /\ ContextAccepted(c) \subseteq ContextImports(c)
    /\ ContextDenied(c) \subseteq ContextImports(c)
    /\ ContextAccepted(c) \cap ContextDenied(c) = {}

NetworkDoesNotWeakenSeedBoundary ==
  /\ RecognitionRequiresImport
  /\ TerminalRecognitionDisjoint
  /\ LocalAuthoritySovereignty
  /\ NoImplicitSuperContext
  /\ PerContextSeedProjectionWellFormed

(***************************************************************************
The Eventually* formulas below are conditional liveness assurance obligations,
not unconditional transport promises.  NetworkExtensionLiveness.cfg checks
them with TLC under FairSpec for the configured finite model.  That bounded
model-checking result is not an unbounded proof for arbitrary federation or
artifact cardinalities.
***************************************************************************)
EventuallyDelivered ==
  \A e \in ExportUniverse : (e \in exports) ~> (e \in delivered)

EventuallyObserved ==
  \A e \in ExportUniverse : (e \in delivered) ~> (e \in imports)

EventuallyResolved ==
  \A e \in ExportUniverse :
    (e \in imports) ~> (e \in accepted \cup denied)

=============================================================================
