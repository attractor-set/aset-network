-------------------------- MODULE NetworkExtension --------------------------
EXTENDS FiniteSets

(***************************************************************************
Independent assurance theory for the complete ASET Network 0.1.0-alpha.3
admission surface.  This module is not a current Network semantic authority.
It models the three externally observable ADMIT_IMPORT outcomes used to audit
expressions of the exact historical subject: fresh admission, exact replay,
and identifier conflict.  Terminal recognition remains Seed-owned.
***************************************************************************)

CONSTANTS Contexts, ImportIDs, Artifacts

ASSUME /\ Contexts # {}
       /\ ImportIDs # {}
       /\ Artifacts # {}

Observation(i, t, a) == [import_id |-> i, target |-> t, artifact |-> a]
ObservationUniverse == [import_id : ImportIDs, target : Contexts, artifact : Artifacts]
ResultCodes == {"IMPORT_ADMITTED", "IDEMPOTENT_REPLAY", "IDENTIFIER_CONFLICT"}
AcceptedResults == {"IMPORT_ADMITTED", "IDEMPOTENT_REPLAY"}

SameIdentifier(S, o) == {x \in S : x.import_id = o.import_id}
FreshIdentifier(S, o) == SameIdentifier(S, o) = {}
ExactReplay(S, o) == o \in S
ConflictingIdentifier(S, o) == /\ SameIdentifier(S, o) # {}
                               /\ o \notin S

VARIABLE imports
vars == <<imports>>

Init == imports = {}

AdmitFresh(o, result) ==
  /\ o \in ObservationUniverse
  /\ o \notin imports
  /\ FreshIdentifier(imports, o)
  /\ imports' = imports \cup {o}
  /\ result = "IMPORT_ADMITTED"

AdmitReplay(o, result) ==
  /\ o \in ObservationUniverse
  /\ ExactReplay(imports, o)
  /\ UNCHANGED imports
  /\ result = "IDEMPOTENT_REPLAY"

RejectConflict(o, result) ==
  /\ o \in ObservationUniverse
  /\ ConflictingIdentifier(imports, o)
  /\ UNCHANGED imports
  /\ result = "IDENTIFIER_CONFLICT"

AdmitImport(o, result) ==
  \/ AdmitFresh(o, result)
  \/ AdmitReplay(o, result)
  \/ RejectConflict(o, result)

NetworkAction ==
  \E o \in ObservationUniverse, result \in ResultCodes : AdmitImport(o, result)
SafetySpec == Init /\ [][NetworkAction]_vars

TypeOK == imports \subseteq ObservationUniverse
ImportsAppendOnly == imports \subseteq imports'

AcceptedResult(result) == result \in AcceptedResults
ProjectedResultStatus(result) == IF result \in ResultCodes THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
ProjectedResultEnforcement(result) == IF result \in ResultCodes THEN "BLOCKED" ELSE "NOT_APPLICABLE"
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
