--------------- MODULE FederationLivenessCompositionRelations ---------------
EXTENDS LivenessContract

FederationCapabilities == {"RETAINED_EXPORT", "DELIVERY", "TARGET_OBSERVATION"}
ProfileParentRelation == FALSE
StateOwnershipTransferred == FALSE
TransitionOwnershipTransferred == FALSE
AuthorityTransferred == FALSE

ProvidesRequiredCapabilities(provided) ==
  RequiredCapabilities \subseteq provided

CompositionBoundaryPreserved(parentRelation, stateOwnershipTransferred, transitionOwnershipTransferred, authorityTransferred) ==
  /\ parentRelation = FALSE
  /\ stateOwnershipTransferred = FALSE
  /\ transitionOwnershipTransferred = FALSE
  /\ authorityTransferred = FALSE

DeliveryWitness(exported, delivered, export) ==
  /\ export \in exported
  /\ export \in delivered

ObservationWitness(delivered, observed, export) ==
  /\ export \in delivered
  /\ export \in observed

ResolutionWitness(observed, resolved, export) ==
  /\ export \in observed
  /\ export \in resolved

ProgressWitness(exported, delivered, observed, resolved, export) ==
  /\ DeliveryWitness(exported, delivered, export)
  /\ ObservationWitness(delivered, observed, export)
  /\ ResolutionWitness(observed, resolved, export)

=============================================================================
