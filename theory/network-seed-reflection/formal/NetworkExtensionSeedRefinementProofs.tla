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

THEOREM FreshProjectionStep ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    AdmitFresh(o, result) =>
      /\ ProjectedRequestMeta' =
           [x \in DOMAIN ProjectedRequestMeta \cup {o} |->
             IF x = o THEN RequestCell(o) ELSE ProjectedRequestMeta[x]]
      /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
PROOF
  BY DEF AdmitFresh, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts, RequestCell

THEOREM FreshRefinesSeedRegisterRequest ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    AdmitFresh(o, result) => BridgeFreshAsSeedRegister(o)
PROOF
  <1>1. SUFFICES ASSUME NEW o \in ObservationUniverse,
                         NEW result \in ResultCodes,
                         AdmitFresh(o, result)
                  PROVE BridgeFreshAsSeedRegister(o)
    OBVIOUS
  <1>2. /\ BridgeBinding(o) \in BridgeBindings
         /\ o.target \in Contexts
         /\ <<o.target, BridgeBinding(o)>> \in BridgeRecognizedAuthorityBindings
    BY <1>1, ObservationBridgeTyping
  <1>3. o \notin Seed!Requests
    BY <1>1, RequestProjectionDomain
       DEF AdmitFresh, Seed!Requests, ProjectedRequestMeta
  <1>4. /\ ProjectedRequestMeta' =
              [x \in Seed!Requests \cup {o} |->
                IF x = o
                THEN [binding |-> BridgeBinding(o), previous |-> NoCommitmentValue]
                ELSE ProjectedRequestMeta[x]]
         /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
    BY <1>1, FreshProjectionStep
       DEF Seed!Requests, RequestCell
  <1>5. NoCommitmentValue = NoCommitmentValue \/ NoCommitmentValue \in {}
    OBVIOUS
  <1>6. QED
    BY <1>1, <1>2, <1>3, <1>4, <1>5
       DEF BridgeFreshAsSeedRegister, Seed!RegisterRequest

THEOREM SeedRegisterRequestIsSeedNext ==
  \A r \in ObservationUniverse,
     b \in BridgeBindings,
     a \in Contexts,
     previous \in {} \cup {NoCommitmentValue} :
    Seed!RegisterRequest(r, b, a, previous) => Seed!Next
PROOF
  BY DEF Seed!Next, Seed!RecognizedSeedTransition

THEOREM FreshRefinesSeedNext ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    AdmitFresh(o, result) => Seed!Next
PROOF
  BY FreshRefinesSeedRegisterRequest,
     ObservationBridgeTyping,
     SeedRegisterRequestIsSeedNext
     DEF BridgeFreshAsSeedRegister

THEOREM ReplayStuttersSeedProjection ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    AdmitReplay(o, result) => UNCHANGED Seed!vars
PROOF
  BY DEF AdmitReplay, Seed!vars, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts

THEOREM ConflictStuttersSeedProjection ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    RejectConflict(o, result) => UNCHANGED Seed!vars
PROOF
  BY DEF RejectConflict, Seed!vars, ProjectedRequestMeta, RequestProjection,
         ProjectedTerminalMeta, ProjectedConflicts

THEOREM ReplayRefinesSeedStutter ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    AdmitReplay(o, result) => [Seed!Next]_Seed!vars
PROOF
  BY ReplayStuttersSeedProjection
     DEF Seed!vars

THEOREM ConflictRefinesSeedStutter ==
  \A o \in ObservationUniverse, result \in ResultCodes :
    RejectConflict(o, result) => [Seed!Next]_Seed!vars
PROOF
  BY ConflictStuttersSeedProjection
     DEF Seed!vars

THEOREM NetworkActionRefinesSeedStepOrStutter ==
  NetworkAction => [Seed!Next]_Seed!vars
PROOF
  BY FreshRefinesSeedNext, ReplayRefinesSeedStutter, ConflictRefinesSeedStutter
     DEF NetworkAction, AdmitImport

THEOREM BoxNetworkActionRefinesBoxSeedNext ==
  [NetworkAction]_vars => [Seed!Next]_Seed!vars
PROOF
  BY NetworkActionRefinesSeedStepOrStutter
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
