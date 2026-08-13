---------------- MODULE NetworkStutteringProofs ----------------
EXTENDS FederationRelations, TLAPS

THEOREM FederationStepPreservesNetworkImports ==
  \A fs, ft, networkBefore, networkAfter :
    FederationStep(fs, ft, networkBefore, networkAfter) =>
      networkAfter = networkBefore
PROOF
  BY DEF FederationStep,
         FederationGenesis,
         MemberJoin,
         RouteGrant,
         ExportArtifact,
         SuspendRoute,
         MemberWithdraw

THEOREM FederationTransitionsStutterOnNetworkImports ==
  FederationStepPreservesNetworkImports
PROOF
  BY FederationStepPreservesNetworkImports

=============================================================================
