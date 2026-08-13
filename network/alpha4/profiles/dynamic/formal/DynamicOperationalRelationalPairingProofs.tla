------------ MODULE DynamicOperationalRelationalPairingProofs ------------
EXTENDS DynamicRestrictedOperationalSemantics, TLAPS

THEOREM ProfileApplicablePairing ==
  \A binding, seedBinding, recognition :
    OperationalProfileApplicable(binding, seedBinding, recognition)
      <=> ProfileApplicable(binding, seedBinding, recognition)
PROOF
  BY DEF OperationalProfileApplicable, ProfileApplicable

THEOREM DynamicProfileNetworkProjectionPairing ==
  \A networkBefore, networkAfter :
    OperationalDynamicProfileNetworkProjection(networkBefore, networkAfter)
      <=> DynamicProfileNetworkProjection(networkBefore, networkAfter)
PROOF
  BY DEF OperationalDynamicProfileNetworkProjection, DynamicProfileNetworkProjection

THEOREM DynamicOperationalRelationalPairing ==
  /\ ProfileApplicablePairing
  /\ DynamicProfileNetworkProjectionPairing
PROOF
  BY ProfileApplicablePairing, DynamicProfileNetworkProjectionPairing

=============================================================================
