---------------------- MODULE NetworkCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/network-extension-model.json
Source SHA-256: sha256:725946f92b6ebe12b805169f45d6a39d66b882ad4dc23120a9733780aea1b9d3
Projection profile: ASET-NETWORK-CANON-TLA-PROJECTION-V3
***************************************************************************)

CONSTANTS Contexts, Artifacts
ASSUME /\ Contexts # {}
       /\ Artifacts # {}

CanonObservation(s, t, a) == [source |-> s, target |-> t, artifact |-> a]
CanonObservationUniverse == [source : Contexts, target : Contexts, artifact : Artifacts]

VARIABLE imports
CanonVars == <<imports>>
CanonInit == imports = {}

CanonAdmitImport(o) ==
  /\ o \in CanonObservationUniverse
  /\ o \notin imports
  /\ imports' = imports \cup {o}

CanonNetworkAction == \E o \in CanonObservationUniverse : CanonAdmitImport(o)
CanonSafetySpec == CanonInit /\ [][CanonNetworkAction]_CanonVars

CanonTypeOK == imports \subseteq CanonObservationUniverse
CanonProjectedStatus(o) == IF o \in imports THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
CanonProjectedEnforcement(o) == IF o \in imports THEN "BLOCKED" ELSE "NOT_APPLICABLE"
CanonAdmissionFailClosed ==
  \A o \in imports :
    /\ CanonProjectedStatus(o) = "UNKNOWN"
    /\ CanonProjectedEnforcement(o) = "BLOCKED"
CanonNoTerminalRecognitionState == TRUE
CanonNoRemoteAuthorityState == TRUE
CanonNetworkDoesNotWeakenSeedBoundary ==
  /\ CanonNoTerminalRecognitionState
  /\ CanonNoRemoteAuthorityState
  /\ CanonAdmissionFailClosed

=============================================================================
