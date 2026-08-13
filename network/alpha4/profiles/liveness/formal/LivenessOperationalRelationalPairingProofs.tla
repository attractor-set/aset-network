----------- MODULE LivenessOperationalRelationalPairingProofs -----------
EXTENDS LivenessRestrictedOperationalSemantics, TLAPS

THEOREM EventuallyDeliveredClaimPairing ==
  \A assumptions :
    OperationalEventuallyDeliveredClaim(assumptions)
      <=> EventuallyDeliveredClaim(assumptions)
PROOF
  BY DEF OperationalEventuallyDeliveredClaim, EventuallyDeliveredClaim

THEOREM EventuallyObservedClaimPairing ==
  \A assumptions :
    OperationalEventuallyObservedClaim(assumptions)
      <=> EventuallyObservedClaim(assumptions)
PROOF
  BY DEF OperationalEventuallyObservedClaim, EventuallyObservedClaim

THEOREM EventuallyTargetLocalSeedResolvedClaimPairing ==
  \A assumptions :
    OperationalEventuallyTargetLocalSeedResolvedClaim(assumptions)
      <=> EventuallyTargetLocalSeedResolvedClaim(assumptions)
PROOF
  BY DEF OperationalEventuallyTargetLocalSeedResolvedClaim,
         EventuallyTargetLocalSeedResolvedClaim

THEOREM ResolvedResultPermittedPairing ==
  \A result :
    OperationalResolvedResultPermitted(result)
      <=> ResolvedResultPermitted(result)
PROOF
  BY DEF OperationalResolvedResultPermitted, ResolvedResultPermitted

THEOREM LivenessOperationalRelationalPairing ==
  /\ EventuallyDeliveredClaimPairing
  /\ EventuallyObservedClaimPairing
  /\ EventuallyTargetLocalSeedResolvedClaimPairing
  /\ ResolvedResultPermittedPairing
PROOF
  BY EventuallyDeliveredClaimPairing,
     EventuallyObservedClaimPairing,
     EventuallyTargetLocalSeedResolvedClaimPairing,
     ResolvedResultPermittedPairing

=============================================================================
