------------- MODULE FederationLivenessContractProofs -------------
EXTENDS FederationLivenessCompositionRelations, TLAPS

THEOREM FederationProvidesRequiredLivenessCapabilities ==
  ProvidesRequiredCapabilities(FederationCapabilities)
PROOF
  BY DEF ProvidesRequiredCapabilities, RequiredCapabilities, FederationCapabilities

THEOREM CompositionTransfersNoOwnership ==
  CompositionBoundaryPreserved(
    ProfileParentRelation,
    StateOwnershipTransferred,
    TransitionOwnershipTransferred,
    AuthorityTransferred)
PROOF
  BY DEF CompositionBoundaryPreserved,
         ProfileParentRelation,
         StateOwnershipTransferred,
         TransitionOwnershipTransferred,
         AuthorityTransferred

THEOREM FederationLivenessCompositionPreservesBoundaries ==
  /\ FederationProvidesRequiredLivenessCapabilities
  /\ CompositionTransfersNoOwnership
PROOF
  BY FederationProvidesRequiredLivenessCapabilities, CompositionTransfersNoOwnership

=============================================================================
