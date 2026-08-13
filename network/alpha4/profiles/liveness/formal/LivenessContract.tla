------------------------ MODULE LivenessContract ------------------------
EXTENDS FiniteSets

RequiredCapabilities == {"RETAINED_EXPORT", "DELIVERY", "TARGET_OBSERVATION"}
LivenessStateAdded == {}
LivenessTransitionsAdded == {}
SeedTerminalResults == {"ALLOW", "BLOCK"}

EventuallyDeliveredClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

EventuallyObservedClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "EVENTUAL_TARGET_OBSERVATION",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

EventuallyTargetLocalSeedResolvedClaim(assumptions) ==
  {"EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
   "EVENTUAL_TARGET_OBSERVATION",
   "TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION",
   "NO_PERMANENT_TARGET_UNAVAILABILITY"} \subseteq assumptions

ResolvedResultPermitted(result) == result \in SeedTerminalResults

=============================================================================
