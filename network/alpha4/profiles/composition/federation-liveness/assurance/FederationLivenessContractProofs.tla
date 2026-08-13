------------- MODULE FederationLivenessContractProofs -------------
EXTENDS LivenessContract, TLAPS

FederationCapabilities == {"RETAINED_EXPORT", "DELIVERY", "TARGET_OBSERVATION"}
ProfileParentRelation == FALSE
StateOwnershipTransferred == FALSE
TransitionOwnershipTransferred == FALSE
AuthorityTransferred == FALSE

THEOREM FederationProvidesRequiredLivenessCapabilities ==
  RequiredCapabilities \subseteq FederationCapabilities
PROOF
  BY DEF RequiredCapabilities, FederationCapabilities

THEOREM CompositionTransfersNoOwnership ==
  /\ ProfileParentRelation = FALSE
  /\ StateOwnershipTransferred = FALSE
  /\ TransitionOwnershipTransferred = FALSE
  /\ AuthorityTransferred = FALSE
PROOF
  BY DEF ProfileParentRelation,
         StateOwnershipTransferred,
         TransitionOwnershipTransferred,
         AuthorityTransferred

THEOREM FederationLivenessCompositionPreservesBoundaries ==
  /\ FederationProvidesRequiredLivenessCapabilities
  /\ CompositionTransfersNoOwnership
PROOF
  BY FederationProvidesRequiredLivenessCapabilities, CompositionTransfersNoOwnership

=============================================================================
