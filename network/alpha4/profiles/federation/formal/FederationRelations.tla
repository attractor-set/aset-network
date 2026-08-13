----------------------- MODULE FederationRelations -----------------------
EXTENDS FiniteSets, NetworkRelations

CONSTANTS FederationIDs, FederationEpochs, Contexts, Artifacts,
          NoFederation, NoEpoch

ASSUME /\ FederationIDs # {}
       /\ FederationEpochs # {}
       /\ Contexts # {}
       /\ Artifacts # {}
       /\ NoFederation \notin FederationIDs
       /\ NoEpoch \notin FederationEpochs

MemberStates == {"ABSENT", "ACTIVE", "WITHDRAWN"}
RouteStates == {"ABSENT", "ACTIVE", "SUSPENDED"}
RouteUniverse == Contexts \X Contexts
Export(source, target, artifact) ==
  [source |-> source, target |-> target, artifact |-> artifact]
ExportUniverse == [source : Contexts, target : Contexts, artifact : Artifacts]

FederationStateType ==
  [federation_id : FederationIDs \cup {NoFederation},
   federation_epoch : FederationEpochs \cup {NoEpoch},
   members : [Contexts -> MemberStates],
   routes : [RouteUniverse -> RouteStates],
   exports : SUBSET ExportUniverse]

EmptyFederationState(fs) ==
  /\ fs \in FederationStateType
  /\ fs.federation_id = NoFederation
  /\ fs.federation_epoch = NoEpoch
  /\ \A c \in Contexts : fs.members[c] = "ABSENT"
  /\ \A r \in RouteUniverse : fs.routes[r] = "ABSENT"
  /\ fs.exports = {}

FederationGenesis(fs, ft, networkBefore, networkAfter, federationId, federationEpoch) ==
  /\ fs \in FederationStateType
  /\ EmptyFederationState(fs)
  /\ federationId \in FederationIDs
  /\ federationEpoch \in FederationEpochs
  /\ ft = [fs EXCEPT
             !.federation_id = federationId,
             !.federation_epoch = federationEpoch]
  /\ networkAfter = networkBefore

MemberJoin(fs, ft, networkBefore, networkAfter, context) ==
  /\ fs \in FederationStateType
  /\ fs.federation_id # NoFederation
  /\ context \in Contexts
  /\ fs.members[context] = "ABSENT"
  /\ ft = [fs EXCEPT !.members[context] = "ACTIVE"]
  /\ networkAfter = networkBefore

RouteGrant(fs, ft, networkBefore, networkAfter, source, target) ==
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

ExportArtifact(fs, ft, networkBefore, networkAfter, source, target, artifact) ==
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

SuspendRoute(fs, ft, networkBefore, networkAfter, source, target) ==
  LET route == <<source, target>>
  IN /\ fs \in FederationStateType
     /\ source \in Contexts
     /\ target \in Contexts
     /\ fs.routes[route] = "ACTIVE"
     /\ ft = [fs EXCEPT !.routes[route] = "SUSPENDED"]
     /\ networkAfter = networkBefore

MemberWithdraw(fs, ft, networkBefore, networkAfter, context) ==
  /\ fs \in FederationStateType
  /\ context \in Contexts
  /\ fs.members[context] = "ACTIVE"
  /\ \A route \in RouteUniverse :
       fs.routes[route] = "ACTIVE" => context \notin {route[1], route[2]}
  /\ ft = [fs EXCEPT !.members[context] = "WITHDRAWN"]
  /\ networkAfter = networkBefore

FederationStep(fs, ft, networkBefore, networkAfter) ==
  \/ \E federationId \in FederationIDs, federationEpoch \in FederationEpochs :
       FederationGenesis(fs, ft, networkBefore, networkAfter, federationId, federationEpoch)
  \/ \E context \in Contexts :
       MemberJoin(fs, ft, networkBefore, networkAfter, context)
  \/ \E source \in Contexts, target \in Contexts :
       RouteGrant(fs, ft, networkBefore, networkAfter, source, target)
  \/ \E source \in Contexts, target \in Contexts, artifact \in Artifacts :
       ExportArtifact(fs, ft, networkBefore, networkAfter, source, target, artifact)
  \/ \E source \in Contexts, target \in Contexts :
       SuspendRoute(fs, ft, networkBefore, networkAfter, source, target)
  \/ \E context \in Contexts :
       MemberWithdraw(fs, ft, networkBefore, networkAfter, context)

=============================================================================
