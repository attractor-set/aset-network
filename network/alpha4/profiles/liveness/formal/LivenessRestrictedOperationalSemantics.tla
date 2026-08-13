--------------- MODULE LivenessRestrictedOperationalSemantics ---------------
EXTENDS LivenessContract

OperationalEventuallyDeliveredClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

OperationalEventuallyObservedClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "EVENTUAL_TARGET_OBSERVATION",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

OperationalEventuallyTargetLocalSeedResolvedClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "EVENTUAL_TARGET_OBSERVATION",
   "TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

OperationalResolvedResultPermitted(result) ==
  result \in SeedTerminalResults

=============================================================================
