---------------- MODULE FederationRestrictedOperationalSemantics ----------------
EXTENDS FederationRelations

OperationalFederationGenesis(fs, ft, networkBefore, networkAfter, federationId, federationEpoch) ==
  /\ fs \in FederationStateType
  /\ EmptyFederationState(fs)
  /\ federationId \in FederationIDs
  /\ federationEpoch \in FederationEpochs
  /\ ft = [fs EXCEPT
             !.federation_id = federationId,
             !.federation_epoch = federationEpoch]
  /\ networkAfter = networkBefore

OperationalMemberJoin(fs, ft, networkBefore, networkAfter, context) ==
  /\ fs \in FederationStateType
  /\ fs.federation_id # NoFederation
  /\ context \in Contexts
  /\ fs.members[context] = "ABSENT"
  /\ ft = [fs EXCEPT !.members[context] = "ACTIVE"]
  /\ networkAfter = networkBefore

OperationalRouteGrant(fs, ft, networkBefore, networkAfter, source, target) ==
  LET route == <<source, target>>
  IN /\ fs \in FederationStateType
     /\ source \in Contexts
     /\ target \in Contexts
     /\ source # target
     /\ fs.members[source] = "ACTIVE"
     /\ fs.members[target] = "ACTIVE"
     /\ fs.routes[route] = "ABSENT"
     /\ ft = [fs EXCEPT !.routes[route] = "ACTIVE"]
     /\ networkAfter = networkBefore

OperationalExportArtifact(fs, ft, networkBefore, networkAfter, source, target, artifact) ==
  LET route == <<source, target>>
      export == Export(source, target, artifact)
  IN /\ fs \in FederationStateType
     /\ source \in Contexts
     /\ target \in Contexts
     /\ artifact \in Artifacts
     /\ fs.routes[route] = "ACTIVE"
     /\ export \notin fs.exports
     /\ ft = [fs EXCEPT !.exports = @ \cup {export}]
     /\ networkAfter = networkBefore

OperationalSuspendRoute(fs, ft, networkBefore, networkAfter, source, target) ==
  LET route == <<source, target>>
  IN /\ fs \in FederationStateType
     /\ source \in Contexts
     /\ target \in Contexts
     /\ fs.routes[route] = "ACTIVE"
     /\ ft = [fs EXCEPT !.routes[route] = "SUSPENDED"]
     /\ networkAfter = networkBefore

OperationalMemberWithdraw(fs, ft, networkBefore, networkAfter, context) ==
  /\ fs \in FederationStateType
  /\ context \in Contexts
  /\ fs.members[context] = "ACTIVE"
  /\ \A route \in RouteUniverse :
       fs.routes[route] = "ACTIVE" => context \notin {route[1], route[2]}
  /\ ft = [fs EXCEPT !.members[context] = "WITHDRAWN"]
  /\ networkAfter = networkBefore

=============================================================================
