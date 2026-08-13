---------------------- MODULE SeedBoundaryProofs ----------------------
EXTENDS NetworkRelations, TLAPS

THEOREM AcceptedAdmissionProjectsOnlyToUnknown ==
  \A result \in ResultCodes :
    AcceptedResult(result) => SeedProjectionRecognition(result) = "UNKNOWN"
PROOF
  BY DEF AcceptedResult, SeedProjectionRecognition

THEOREM NetworkNeverPermitsSeedEffect ==
  \A result \in ResultCodes : SeedProjectionEffectPermitted(result) = FALSE
PROOF
  BY DEF SeedProjectionEffectPermitted

THEOREM NetworkAdmissionPreservesSeedRecognitionBoundary ==
  /\ AcceptedAdmissionProjectsOnlyToUnknown
  /\ NetworkNeverPermitsSeedEffect
PROOF
  BY AcceptedAdmissionProjectsOnlyToUnknown, NetworkNeverPermitsSeedEffect

=============================================================================
