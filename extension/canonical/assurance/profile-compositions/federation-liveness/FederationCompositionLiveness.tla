------------------- MODULE FederationCompositionLiveness -------------------
EXTENDS FederationProfile

(***************************************************************************
Bounded assurance for composition of two independent optional profiles:
ASET-NETWORK-FEDERATION-PROFILE-V1 and ASET-NETWORK-LIVENESS-V1, over the
Network admission core and target-local Seed resolution.  Neither profile is
the parent of the other, and composition transfers no state or Authority ownership.

`Deliver(e)`, `Observe(e)` and `Resolve(e)` are composition-assurance witnesses,
not new Federation-owned transitions. `Resolve(e)` is specifically an assurance
witness that the pinned target-local Seed eventually reaches a terminal result
when that local progress assumption is claimed.
***************************************************************************)

VARIABLES delivered, imports, resolved
compositionVars == <<federationCreated, memberStatus, routes, activeRoutes, exports,
                     delivered, imports, resolved>>

CompositionInit ==
  /\ Init
  /\ delivered = {}
  /\ imports = {}
  /\ resolved = {}

ProfileGenesis == Genesis /\ UNCHANGED <<delivered, imports, resolved>>
ProfileJoin(c) == Join(c) /\ UNCHANGED <<delivered, imports, resolved>>
ProfileGrantRoute(s, t) == GrantRoute(s, t) /\ UNCHANGED <<delivered, imports, resolved>>
ProfileExportArtifact(s, t, a) ==
  ExportArtifact(s, t, a) /\ UNCHANGED <<delivered, imports, resolved>>
ProfileSuspendRoute(s, t) == SuspendRoute(s, t) /\ UNCHANGED <<delivered, imports, resolved>>
ProfileWithdraw(c) == Withdraw(c) /\ UNCHANGED <<delivered, imports, resolved>>

Deliver(e) ==
  /\ e \in exports
  /\ e \notin delivered
  /\ delivered' = delivered \cup {e}
  /\ UNCHANGED <<federationCreated, memberStatus, routes, activeRoutes, exports,
                  imports, resolved>>

Observe(e) ==
  /\ e \in delivered
  /\ e \notin imports
  /\ memberStatus[e.target] = "ACTIVE"
  /\ imports' = imports \cup {e}
  /\ UNCHANGED <<federationCreated, memberStatus, routes, activeRoutes, exports,
                  delivered, resolved>>

Resolve(e) ==
  /\ e \in imports
  /\ e \notin resolved
  /\ resolved' = resolved \cup {e}
  /\ UNCHANGED <<federationCreated, memberStatus, routes, activeRoutes, exports,
                  delivered, imports>>

CompositionAction ==
  \/ ProfileGenesis
  \/ \E c \in Contexts : ProfileJoin(c)
  \/ \E s \in Contexts, t \in Contexts : ProfileGrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ProfileExportArtifact(s, t, a)
  \/ \E s \in Contexts, t \in Contexts : ProfileSuspendRoute(s, t)
  \/ \E c \in Contexts : ProfileWithdraw(c)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E e \in ExportUniverse : Observe(e)
  \/ \E e \in ExportUniverse : Resolve(e)

(***************************************************************************
NET-LIVE-A-004 excludes permanent target withdrawal while a progress claim is
active. Safety still permits ProfileWithdraw through CompositionAction, but
the liveness harness deliberately excludes it from the progress relation.
***************************************************************************)
CompositionProgressAction ==
  \/ ProfileGenesis
  \/ \E c \in Contexts : ProfileJoin(c)
  \/ \E s \in Contexts, t \in Contexts : ProfileGrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ProfileExportArtifact(s, t, a)
  \/ \E s \in Contexts, t \in Contexts : ProfileSuspendRoute(s, t)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E e \in ExportUniverse : Observe(e)
  \/ \E e \in ExportUniverse : Resolve(e)

FairSpec ==
  /\ CompositionInit
  /\ [][CompositionProgressAction]_compositionVars
  /\ \A e \in ExportUniverse : WF_compositionVars(Deliver(e))
  /\ \A e \in ExportUniverse : WF_compositionVars(Observe(e))
  /\ \A e \in ExportUniverse : WF_compositionVars(Resolve(e))

CompositionTypeOK ==
  /\ TypeOK
  /\ delivered \subseteq exports
  /\ imports \subseteq delivered
  /\ resolved \subseteq imports

ResolutionRequiresImport == resolved \subseteq imports

PendingProgress ==
  {e \in exports : e \notin delivered}
    \cup {e \in delivered : e \notin imports}
    \cup {e \in imports : e \notin resolved}

NoPendingProgressDeadlock ==
  PendingProgress = {} \/ ENABLED CompositionProgressAction

EventuallyDelivered ==
  \A e \in ExportUniverse : (e \in exports) ~> (e \in delivered)

EventuallyObserved ==
  \A e \in ExportUniverse : (e \in delivered) ~> (e \in imports)

EventuallyResolved ==
  \A e \in ExportUniverse : (e \in imports) ~> (e \in resolved)

=============================================================================
