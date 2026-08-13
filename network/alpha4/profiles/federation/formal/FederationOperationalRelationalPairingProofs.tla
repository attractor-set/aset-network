------------ MODULE FederationOperationalRelationalPairingProofs ------------
EXTENDS FederationRestrictedOperationalSemantics, TLAPS

THEOREM FederationGenesisPairing ==
  \A fs, ft, networkBefore, networkAfter, federationId, federationEpoch :
    OperationalFederationGenesis(fs, ft, networkBefore, networkAfter, federationId, federationEpoch)
      <=> FederationGenesis(fs, ft, networkBefore, networkAfter, federationId, federationEpoch)
PROOF
  BY DEF OperationalFederationGenesis, FederationGenesis

THEOREM MemberJoinPairing ==
  \A fs, ft, networkBefore, networkAfter, context :
    OperationalMemberJoin(fs, ft, networkBefore, networkAfter, context)
      <=> MemberJoin(fs, ft, networkBefore, networkAfter, context)
PROOF
  BY DEF OperationalMemberJoin, MemberJoin

THEOREM RouteGrantPairing ==
  \A fs, ft, networkBefore, networkAfter, source, target :
    OperationalRouteGrant(fs, ft, networkBefore, networkAfter, source, target)
      <=> RouteGrant(fs, ft, networkBefore, networkAfter, source, target)
PROOF
  BY DEF OperationalRouteGrant, RouteGrant

THEOREM ExportArtifactPairing ==
  \A fs, ft, networkBefore, networkAfter, source, target, artifact :
    OperationalExportArtifact(fs, ft, networkBefore, networkAfter, source, target, artifact)
      <=> ExportArtifact(fs, ft, networkBefore, networkAfter, source, target, artifact)
PROOF
  BY DEF OperationalExportArtifact, ExportArtifact

THEOREM SuspendRoutePairing ==
  \A fs, ft, networkBefore, networkAfter, source, target :
    OperationalSuspendRoute(fs, ft, networkBefore, networkAfter, source, target)
      <=> SuspendRoute(fs, ft, networkBefore, networkAfter, source, target)
PROOF
  BY DEF OperationalSuspendRoute, SuspendRoute

THEOREM MemberWithdrawPairing ==
  \A fs, ft, networkBefore, networkAfter, context :
    OperationalMemberWithdraw(fs, ft, networkBefore, networkAfter, context)
      <=> MemberWithdraw(fs, ft, networkBefore, networkAfter, context)
PROOF
  BY DEF OperationalMemberWithdraw, MemberWithdraw

THEOREM FederationOperationalRelationalPairing ==
  /\ FederationGenesisPairing
  /\ MemberJoinPairing
  /\ RouteGrantPairing
  /\ ExportArtifactPairing
  /\ SuspendRoutePairing
  /\ MemberWithdrawPairing
PROOF
  BY FederationGenesisPairing,
     MemberJoinPairing,
     RouteGrantPairing,
     ExportArtifactPairing,
     SuspendRoutePairing,
     MemberWithdrawPairing

=============================================================================
