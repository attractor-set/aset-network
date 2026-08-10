------------------- MODULE NetworkCanonRefinementProofs -------------------
EXTENDS NetworkExtension, TLAPS

Canon == INSTANCE NetworkCanonProjection
  WITH Contexts <- Contexts,
       Artifacts <- Artifacts,
       imports <- imports

THEOREM NetworkCanonCoreAlgebraEquivalent ==
  ObservationUniverse = Canon!CanonObservationUniverse
PROOF
  BY DEF ObservationUniverse, Canon!CanonObservationUniverse

THEOREM NetworkCoreSafetyPredicatesEquivalentToCanonProjection ==
  /\ TypeOK <=> Canon!CanonTypeOK
  /\ AdmissionFailClosed <=> Canon!CanonAdmissionFailClosed
  /\ NoTerminalRecognitionState <=> Canon!CanonNoTerminalRecognitionState
  /\ NoRemoteAuthorityState <=> Canon!CanonNoRemoteAuthorityState
  /\ NetworkDoesNotWeakenSeedBoundary
       <=> Canon!CanonNetworkDoesNotWeakenSeedBoundary
PROOF
  BY DEF TypeOK, AdmissionFailClosed, ProjectedStatus, ProjectedEnforcement,
         NoTerminalRecognitionState, NoRemoteAuthorityState,
         NetworkDoesNotWeakenSeedBoundary, ObservationUniverse,
         Canon!CanonTypeOK, Canon!CanonAdmissionFailClosed,
         Canon!CanonProjectedStatus, Canon!CanonProjectedEnforcement,
         Canon!CanonNoTerminalRecognitionState, Canon!CanonNoRemoteAuthorityState,
         Canon!CanonNetworkDoesNotWeakenSeedBoundary,
         Canon!CanonObservationUniverse

THEOREM NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection ==
  SafetySpec <=> Canon!CanonSafetySpec
PROOF
  BY DEF SafetySpec, Init, NetworkAction, AdmitImport, vars,
         ObservationUniverse,
         Canon!CanonSafetySpec, Canon!CanonInit, Canon!CanonNetworkAction,
         Canon!CanonAdmitImport, Canon!CanonVars, Canon!CanonObservationUniverse

=============================================================================
