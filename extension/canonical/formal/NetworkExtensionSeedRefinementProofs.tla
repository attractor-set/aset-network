------------- MODULE NetworkExtensionSeedRefinementProofs -------------
EXTENDS NetworkExtensionSeedRefinement, TLAPS

THEOREM RequestProjectionDomain ==
  \A S : DOMAIN RequestProjection(S) = S
PROOF
  BY DEF RequestProjection

THEOREM ObservationBridgeTyping ==
  \A o \in ObservationUniverse :
    /\ BridgeBinding(o) \in BridgeBindings
    /\ o.target \in Contexts
    /\ <<o.target, BridgeBinding(o)>> \in BridgeRecognizedAuthorityBindings
PROOF
  BY DEF ObservationUniverse, BridgeBinding, BridgeBindings,
         BridgeRecognizedAuthorityBindings

THEOREM InitRefinesSeedInit ==
  Init => Seed!Init
PROOF
  BY DEF Init, Seed!Init, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts

THEOREM AdmitProjectionStep ==
  \A o \in ObservationUniverse :
    AdmitImport(o) =>
      /\ ProjectedRequestMeta' =
           [x \in DOMAIN ProjectedRequestMeta \cup {o} |->
             IF x = o THEN RequestCell(o) ELSE ProjectedRequestMeta[x]]
      /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
PROOF
  BY DEF AdmitImport, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts, RequestCell

THEOREM AdmitRefinesSeedRegisterRequest ==
  \A o \in ObservationUniverse :
    AdmitImport(o) => BridgeAdmitAsSeedRegister(o)
PROOF
  <1>1. SUFFICES ASSUME NEW o \in ObservationUniverse, AdmitImport(o)
                  PROVE BridgeAdmitAsSeedRegister(o)
    OBVIOUS
  <1>2. /\ BridgeBinding(o) \in BridgeBindings
         /\ o.target \in Contexts
         /\ <<o.target, BridgeBinding(o)>> \in BridgeRecognizedAuthorityBindings
    BY <1>1, ObservationBridgeTyping
  <1>3. o \notin Seed!Requests
    BY <1>1, RequestProjectionDomain
       DEF AdmitImport, Seed!Requests, ProjectedRequestMeta
  <1>4. /\ ProjectedRequestMeta' =
              [x \in Seed!Requests \cup {o} |->
                IF x = o
                THEN [binding |-> BridgeBinding(o), previous |-> NoCommitmentValue]
                ELSE ProjectedRequestMeta[x]]
         /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
    BY <1>1, AdmitProjectionStep
       DEF Seed!Requests, RequestCell
  <1>5. NoCommitmentValue = NoCommitmentValue \/ NoCommitmentValue \in {}
    OBVIOUS
  <1>6. QED
    BY <1>1, <1>2, <1>3, <1>4, <1>5
       DEF BridgeAdmitAsSeedRegister, Seed!RegisterRequest

THEOREM SeedRegisterRequestIsSeedNext ==
  \A r \in ObservationUniverse,
     b \in BridgeBindings,
     a \in Contexts,
     previous \in {} \cup {NoCommitmentValue} :
    Seed!RegisterRequest(r, b, a, previous) => Seed!Next
PROOF
  BY DEF Seed!Next, Seed!RecognizedSeedTransition

THEOREM AdmitImportRefinesSeedNext ==
  \A o \in ObservationUniverse :
    AdmitImport(o) => Seed!Next
PROOF
  BY AdmitRefinesSeedRegisterRequest,
     ObservationBridgeTyping,
     SeedRegisterRequestIsSeedNext
     DEF BridgeAdmitAsSeedRegister

THEOREM NetworkActionRefinesSeedStep ==
  NetworkAction => Seed!Next
PROOF
  BY AdmitImportRefinesSeedNext
     DEF NetworkAction

THEOREM BoxNetworkActionRefinesBoxSeedNext ==
  [NetworkAction]_vars => [Seed!Next]_Seed!vars
PROOF
  BY NetworkActionRefinesSeedStep
     DEF vars, Seed!vars, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts

THEOREM NetworkExtensionRefinesSeedSafetySpec ==
  SafetySpec => Seed!Spec
PROOF
  BY PTL, InitRefinesSeedInit, BoxNetworkActionRefinesBoxSeedNext
     DEF SafetySpec, Seed!Spec

THEOREM NetworkProjectionMatchesSeedResolution ==
  \A o \in ObservationUniverse :
    /\ NetworkProjectedSeedResolution(o) = ProjectedSeedResolution(o)
    /\ NetworkProjectedSeedEffectPermitted(o) = ProjectedSeedEffectPermitted(o)
PROOF
  BY DEF NetworkProjectedSeedResolution,
         NetworkProjectedSeedEffectPermitted,
         ProjectedSeedResolution,
         ProjectedSeedEffectPermitted,
         Seed!ResolutionOf, Seed!EffectPermitted,
         Seed!Requests, Seed!TerminalRequests,
         ProjectedRequestMeta, ProjectedTerminalMeta,
         ProjectedConflicts, RequestProjection

=============================================================================
