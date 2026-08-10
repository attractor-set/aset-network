-------------------------- MODULE NetworkExtension --------------------------
EXTENDS FiniteSets

(***************************************************************************
Normative assurance model for ASET Network 0.1.0-alpha.3.
The universal Network core owns exactly one semantic state component,
imports, and exactly one state-changing action, AdmitImport.
Federation lifecycle is an optional profile. Terminal recognition is Seed-owned.
***************************************************************************)

CONSTANTS Contexts, Artifacts

ASSUME /\ Contexts # {}
       /\ Artifacts # {}

Observation(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
ObservationUniverse == [source : Contexts, target : Contexts, artifact : Artifacts]

VARIABLE imports
vars == <<imports>>

Init == imports = {}

AdmitImport(o) ==
  /\ o \in ObservationUniverse
  /\ o \notin imports
  /\ imports' = imports \cup {o}

NetworkAction == \E o \in ObservationUniverse : AdmitImport(o)
SafetySpec == Init /\ [][NetworkAction]_vars

TypeOK == imports \subseteq ObservationUniverse
ImportsAppendOnly == imports \subseteq imports'

ProjectedStatus(o) == IF o \in imports THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
ProjectedEnforcement(o) == IF o \in imports THEN "BLOCKED" ELSE "NOT_APPLICABLE"

AdmissionFailClosed ==
  \A o \in imports :
    /\ ProjectedStatus(o) = "UNKNOWN"
    /\ ProjectedEnforcement(o) = "BLOCKED"

NoTerminalRecognitionState == TRUE
NoRemoteAuthorityState == TRUE
NetworkDoesNotWeakenSeedBoundary ==
  /\ NoTerminalRecognitionState
  /\ NoRemoteAuthorityState
  /\ AdmissionFailClosed

MinimalNetworkSafety ==
  /\ TypeOK
  /\ AdmissionFailClosed
  /\ NoTerminalRecognitionState
  /\ NoRemoteAuthorityState
  /\ NetworkDoesNotWeakenSeedBoundary

=============================================================================
