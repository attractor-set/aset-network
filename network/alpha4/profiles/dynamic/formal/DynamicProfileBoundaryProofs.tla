------------------- MODULE DynamicProfileBoundaryProofs -------------------
EXTENDS DynamicProfileRelations, TLAPS

THEOREM ApplicabilityRequiresExactTargetLocalAllow ==
  \A binding, seedBinding, recognition :
    ProfileApplicable(binding, seedBinding, recognition) =>
      /\ seedBinding = ProjectSeedBinding(binding)
      /\ recognition = "ALLOW"
PROOF
  BY DEF ProfileApplicable

THEOREM DynamicProfileAddsNoNetworkMutation ==
  \A networkBefore, networkAfter :
    DynamicProfileNetworkProjection(networkBefore, networkAfter) =>
      networkAfter = networkBefore
PROOF
  BY DEF DynamicProfileNetworkProjection

THEOREM DynamicProfilesPreserveNetworkAndLocalAuthority ==
  /\ ApplicabilityRequiresExactTargetLocalAllow
  /\ DynamicProfileAddsNoNetworkMutation
PROOF
  BY ApplicabilityRequiresExactTargetLocalAllow, DynamicProfileAddsNoNetworkMutation

=============================================================================
