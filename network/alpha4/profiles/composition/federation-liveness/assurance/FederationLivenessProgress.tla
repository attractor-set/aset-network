---------------- MODULE FederationLivenessProgress ----------------
EXTENDS FederationRelations

CONSTANTS InitialNetworkImports
VARIABLES federation, networkImports, delivered, observed, resolved
vars == <<federation, networkImports, delivered, observed, resolved>>

Init ==
  /\ EmptyFederationState(federation)
  /\ networkImports = InitialNetworkImports
  /\ delivered = {}
  /\ observed = {}
  /\ resolved = {}

ProfileGenesis(federationId, federationEpoch) ==
  /\ FederationGenesis(
       federation,
       federation',
       networkImports,
       networkImports',
       federationId,
       federationEpoch)
  /\ UNCHANGED <<delivered, observed, resolved>>

ProfileJoin(context) ==
  /\ MemberJoin(federation, federation', networkImports, networkImports', context)
  /\ UNCHANGED <<delivered, observed, resolved>>

ProfileGrantRoute(source, target) ==
  /\ RouteGrant(federation, federation', networkImports, networkImports', source, target)
  /\ UNCHANGED <<delivered, observed, resolved>>

ProfileExportArtifact(source, target, artifact) ==
  /\ ExportArtifact(
       federation,
       federation',
       networkImports,
       networkImports',
       source,
       target,
       artifact)
  /\ UNCHANGED <<delivered, observed, resolved>>

ProfileSuspendRoute(source, target) ==
  /\ SuspendRoute(federation, federation', networkImports, networkImports', source, target)
  /\ UNCHANGED <<delivered, observed, resolved>>

ProgressProfileStep ==
  \/ \E federationId \in FederationIDs, federationEpoch \in FederationEpochs :
       ProfileGenesis(federationId, federationEpoch)
  \/ \E context \in Contexts : ProfileJoin(context)
  \/ \E source \in Contexts, target \in Contexts : ProfileGrantRoute(source, target)
  \/ \E source \in Contexts, target \in Contexts, artifact \in Artifacts :
       ProfileExportArtifact(source, target, artifact)
  \/ \E source \in Contexts, target \in Contexts : ProfileSuspendRoute(source, target)

Deliver(export) ==
  /\ export \in federation.exports
  /\ export \notin delivered
  /\ delivered' = delivered \cup {export}
  /\ UNCHANGED <<federation, networkImports, observed, resolved>>

Observe(export) ==
  /\ export \in delivered
  /\ export \notin observed
  /\ federation.members[export.target] = "ACTIVE"
  /\ observed' = observed \cup {export}
  /\ UNCHANGED <<federation, networkImports, delivered, resolved>>

Resolve(export) ==
  /\ export \in observed
  /\ export \notin resolved
  /\ resolved' = resolved \cup {export}
  /\ UNCHANGED <<federation, networkImports, delivered, observed>>

ProgressAction ==
  \/ ProgressProfileStep
  \/ \E export \in ExportUniverse : Deliver(export)
  \/ \E export \in ExportUniverse : Observe(export)
  \/ \E export \in ExportUniverse : Resolve(export)

FairSpec ==
  /\ Init
  /\ [][ProgressAction]_vars
  /\ \A export \in ExportUniverse : WF_vars(Deliver(export))
  /\ \A export \in ExportUniverse : WF_vars(Observe(export))
  /\ \A export \in ExportUniverse : WF_vars(Resolve(export))

TypeOK ==
  /\ federation \in FederationStateType
  /\ networkImports = InitialNetworkImports
  /\ delivered \subseteq federation.exports
  /\ observed \subseteq delivered
  /\ resolved \subseteq observed

EventuallyDelivered ==
  \A export \in ExportUniverse : (export \in federation.exports) ~> (export \in delivered)

EventuallyObserved ==
  \A export \in ExportUniverse : (export \in delivered) ~> (export \in observed)

EventuallyResolved ==
  \A export \in ExportUniverse : (export \in observed) ~> (export \in resolved)

=============================================================================
