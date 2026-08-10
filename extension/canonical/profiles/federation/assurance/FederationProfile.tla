-------------------------- MODULE FederationProfile --------------------------
EXTENDS FiniteSets

(***************************************************************************
TLC safety assurance specification for ASET-NETWORK-FEDERATION-PROFILE-V1.

The profile is optional and has no authority to recognize evidence in a target
Context.  This assurance specification therefore contains federation lifecycle state only; it
contains no Network imports and no Seed terminal-recognition state.
***************************************************************************)

CONSTANTS Contexts, Artifacts
ASSUME /\ Contexts # {}
       /\ Artifacts # {}

MemberStates == {"ABSENT", "ACTIVE", "WITHDRAWN"}
Export(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
ExportUniverse == [source : Contexts, target : Contexts, artifact : Artifacts]
RouteUniverse == Contexts \X Contexts

VARIABLES federationCreated, memberStatus, routes, activeRoutes, exports
vars == <<federationCreated, memberStatus, routes, activeRoutes, exports>>

Init ==
  /\ federationCreated = FALSE
  /\ memberStatus = [c \in Contexts |-> "ABSENT"]
  /\ routes = {}
  /\ activeRoutes = {}
  /\ exports = {}

Genesis ==
  /\ ~federationCreated
  /\ federationCreated' = TRUE
  /\ UNCHANGED <<memberStatus, routes, activeRoutes, exports>>

Join(c) ==
  /\ federationCreated
  /\ c \in Contexts
  /\ memberStatus[c] = "ABSENT"
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "ACTIVE"]
  /\ UNCHANGED <<federationCreated, routes, activeRoutes, exports>>

GrantRoute(s, t) ==
  /\ federationCreated
  /\ s \in Contexts
  /\ t \in Contexts
  /\ s # t
  /\ memberStatus[s] = "ACTIVE"
  /\ memberStatus[t] = "ACTIVE"
  /\ <<s, t>> \notin routes
  /\ routes' = routes \cup {<<s, t>>}
  /\ activeRoutes' = activeRoutes \cup {<<s, t>>}
  /\ UNCHANGED <<federationCreated, memberStatus, exports>>

ExportArtifact(s, t, a) ==
  LET e == Export(s, t, a)
  IN /\ federationCreated
     /\ <<s, t>> \in activeRoutes
     /\ e \notin exports
     /\ exports' = exports \cup {e}
     /\ UNCHANGED <<federationCreated, memberStatus, routes, activeRoutes>>

SuspendRoute(s, t) ==
  /\ <<s, t>> \in activeRoutes
  /\ activeRoutes' = activeRoutes \ {<<s, t>>}
  /\ UNCHANGED <<federationCreated, memberStatus, routes, exports>>

Withdraw(c) ==
  /\ c \in Contexts
  /\ memberStatus[c] = "ACTIVE"
  /\ \A r \in activeRoutes : c \notin {r[1], r[2]}
  /\ memberStatus' = [memberStatus EXCEPT ![c] = "WITHDRAWN"]
  /\ UNCHANGED <<federationCreated, routes, activeRoutes, exports>>

ProfileAction ==
  \/ Genesis
  \/ \E c \in Contexts : Join(c)
  \/ \E s \in Contexts, t \in Contexts : GrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ExportArtifact(s, t, a)
  \/ \E s \in Contexts, t \in Contexts : SuspendRoute(s, t)
  \/ \E c \in Contexts : Withdraw(c)

SafetySpec == Init /\ [][ProfileAction]_vars

TypeOK ==
  /\ federationCreated \in BOOLEAN
  /\ memberStatus \in [Contexts -> MemberStates]
  /\ routes \subseteq RouteUniverse
  /\ activeRoutes \subseteq routes
  /\ exports \subseteq ExportUniverse

NoSelfRoute == \A r \in routes : r[1] # r[2]

ActiveRouteMembersActive ==
  \A r \in activeRoutes :
    /\ memberStatus[r[1]] = "ACTIVE"
    /\ memberStatus[r[2]] = "ACTIVE"

ExportBindingPreserved ==
  \A e \in exports :
    /\ <<e.source, e.target>> \in routes
    /\ e.source # e.target

=============================================================================
