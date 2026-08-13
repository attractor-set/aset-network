---------- MODULE FederationLivenessRestrictedOperationalSemantics ----------
EXTENDS FederationLivenessCompositionRelations

OperationalProvidesRequiredCapabilities(provided) ==
  RequiredCapabilities \subseteq provided

OperationalCompositionBoundaryPreserved(parentRelation, stateOwnershipTransferred, transitionOwnershipTransferred, authorityTransferred) ==
  /\ parentRelation = FALSE
  /\ stateOwnershipTransferred = FALSE
  /\ transitionOwnershipTransferred = FALSE
  /\ authorityTransferred = FALSE

OperationalDeliveryWitness(exported, delivered, export) ==
  /\ export \in exported
  /\ export \in delivered

OperationalObservationWitness(delivered, observed, export) ==
  /\ export \in delivered
  /\ export \in observed

OperationalResolutionWitness(observed, resolved, export) ==
  /\ export \in observed
  /\ export \in resolved

OperationalProgressWitness(exported, delivered, observed, resolved, export) ==
  /\ OperationalDeliveryWitness(exported, delivered, export)
  /\ OperationalObservationWitness(delivered, observed, export)
  /\ OperationalResolutionWitness(observed, resolved, export)

=============================================================================
