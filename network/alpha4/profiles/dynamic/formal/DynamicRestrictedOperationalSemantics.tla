--------------- MODULE DynamicRestrictedOperationalSemantics ---------------
EXTENDS DynamicProfileRelations

OperationalProfileApplicable(binding, seedBinding, recognition) ==
  /\ binding \in ProfileBindingType
  /\ seedBinding \in SeedBindingType
  /\ seedBinding = ProjectSeedBinding(binding)
  /\ recognition = "ALLOW"

OperationalDynamicProfileNetworkProjection(networkBefore, networkAfter) ==
  networkAfter = networkBefore

=============================================================================
