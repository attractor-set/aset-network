------- MODULE FederationLivenessOperationalRelationalPairingProofs -------
EXTENDS FederationLivenessRestrictedOperationalSemantics, TLAPS

THEOREM RequiredCapabilitiesPairing ==
  \A provided :
    OperationalProvidesRequiredCapabilities(provided)
      <=> ProvidesRequiredCapabilities(provided)
PROOF
  BY DEF OperationalProvidesRequiredCapabilities, ProvidesRequiredCapabilities

THEOREM CompositionBoundaryPairing ==
  \A parentRelation,
     stateOwnershipTransferred,
     transitionOwnershipTransferred,
     authorityTransferred :
    OperationalCompositionBoundaryPreserved(
      parentRelation,
      stateOwnershipTransferred,
      transitionOwnershipTransferred,
      authorityTransferred)
      <=> CompositionBoundaryPreserved(
            parentRelation,
            stateOwnershipTransferred,
            transitionOwnershipTransferred,
            authorityTransferred)
PROOF
  BY DEF OperationalCompositionBoundaryPreserved, CompositionBoundaryPreserved

THEOREM DeliveryWitnessPairing ==
  \A exported, delivered, export :
    OperationalDeliveryWitness(exported, delivered, export)
      <=> DeliveryWitness(exported, delivered, export)
PROOF
  BY DEF OperationalDeliveryWitness, DeliveryWitness

THEOREM ObservationWitnessPairing ==
  \A delivered, observed, export :
    OperationalObservationWitness(delivered, observed, export)
      <=> ObservationWitness(delivered, observed, export)
PROOF
  BY DEF OperationalObservationWitness, ObservationWitness

THEOREM ResolutionWitnessPairing ==
  \A observed, resolved, export :
    OperationalResolutionWitness(observed, resolved, export)
      <=> ResolutionWitness(observed, resolved, export)
PROOF
  BY DEF OperationalResolutionWitness, ResolutionWitness

THEOREM ProgressWitnessPairing ==
  \A exported, delivered, observed, resolved, export :
    OperationalProgressWitness(exported, delivered, observed, resolved, export)
      <=> ProgressWitness(exported, delivered, observed, resolved, export)
PROOF
  BY DEF OperationalProgressWitness,
         ProgressWitness,
         OperationalDeliveryWitness,
         DeliveryWitness,
         OperationalObservationWitness,
         ObservationWitness,
         OperationalResolutionWitness,
         ResolutionWitness

THEOREM FederationLivenessOperationalRelationalPairing ==
  /\ RequiredCapabilitiesPairing
  /\ CompositionBoundaryPairing
  /\ DeliveryWitnessPairing
  /\ ObservationWitnessPairing
  /\ ResolutionWitnessPairing
  /\ ProgressWitnessPairing
PROOF
  BY RequiredCapabilitiesPairing,
     CompositionBoundaryPairing,
     DeliveryWitnessPairing,
     ObservationWitnessPairing,
     ResolutionWitnessPairing,
     ProgressWitnessPairing

=============================================================================
