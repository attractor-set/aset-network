---------------- MODULE NetworkExtensionSeedRefinement ----------------
EXTENDS NetworkExtension

NoCommitmentValue == "NETWORK-NO-COMMITMENT"
BridgeBindings == Contexts \X Artifacts
BridgeBinding(o) == <<o.target, o.artifact>>
BridgeRecognizedAuthorityBindings ==
  {p \in Contexts \X BridgeBindings : p[1] = p[2][1]}

RequestCell(o) ==
  [binding |-> BridgeBinding(o), previous |-> NoCommitmentValue]
RequestProjection(S) == [o \in S |-> RequestCell(o)]
ProjectedRequestMeta == RequestProjection(imports)
ProjectedTerminalMeta == [r \in {} |-> r]
ProjectedConflicts == {}

Seed == INSTANCE SeedResolution
  WITH ResolutionIds <- ObservationUniverse,
       Bindings <- BridgeBindings,
       Authorities <- Contexts,
       TerminalCommitments <- {},
       RecognizedTerminalCommitments <- {},
       NoCommitment <- NoCommitmentValue,
       RecognizedAuthorityBindings <- BridgeRecognizedAuthorityBindings,
       requestMeta <- ProjectedRequestMeta,
       terminalMeta <- ProjectedTerminalMeta,
       conflicts <- ProjectedConflicts

BridgeAdmitAsSeedRegister(o) ==
  Seed!RegisterRequest(o, BridgeBinding(o), o.target, NoCommitmentValue)

ProjectedSeedResolution(o) == Seed!ResolutionOf(o)
ProjectedSeedEffectPermitted(o) == Seed!EffectPermitted(o)
NetworkProjectedSeedResolution(o) == IF o \in imports THEN "UNKNOWN" ELSE "UNKNOWN"
NetworkProjectedSeedEffectPermitted(o) == FALSE

BridgeProjectionWellFormed ==
  /\ DOMAIN ProjectedRequestMeta = imports
  /\ DOMAIN ProjectedTerminalMeta = {}
  /\ ProjectedConflicts = {}

=============================================================================
