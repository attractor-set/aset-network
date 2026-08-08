------------- MODULE NetworkExtensionSeedRefinementProofs -------------
EXTENDS NetworkExtensionSeedRefinement, TLAPS

(***************************************************************************
TLAPS proof bridge to the exact pinned upstream SeedResolution.tla module.

This proof deliberately follows the proof shape used by SeedResolutionProofs:
  - establish small pointwise/domain facts first;
  - prove each recognized action separately;
  - compose recognized actions into one step theorem;
  - lift the step theorem to the boxed temporal specification with PTL.

The bridge proves only the declared abstraction mapping. It does not prove
wire-schema equivalence, cryptographic Binding construction, concrete Authority
identity construction, transport properties, or implementation refinement.
The machine-readable Network canon and pinned Seed canon retain normative
precedence over these assurance artifacts.
***************************************************************************)

THEOREM RequestProjectionDomain ==
  \A S : DOMAIN RequestProjection(S) = S
PROOF
  BY DEF RequestProjection


THEOREM TerminalProjectionDomain ==
  \A accSet, denySet :
    DOMAIN TerminalProjection(accSet, denySet) = accSet \cup denySet
PROOF
  BY DEF TerminalProjection


(***************************************************************************
Do not state unconstrained function extensionality over arbitrary TLA+ values.
TLAPS' function-equality rule requires both operands to be known functions.
The two update lemmas below compare explicit function constructors, so their
final equality step exposes TerminalProjection to Isabelle and lets the
Functions theory establish functionhood before applying extensionality.
***************************************************************************)
THEOREM TerminalProjectionAppendAllow ==
  \A accSet, denySet, e :
    e \notin accSet \cup denySet =>
      TerminalProjection(accSet \cup {e}, denySet) =
        [x \in accSet \cup denySet \cup {e} |->
          IF x = e
          THEN TerminalCell(e, "ALLOW")
          ELSE TerminalProjection(accSet, denySet)[x]]
PROOF
  <1>1. SUFFICES ASSUME NEW accSet, NEW denySet, NEW e,
                          e \notin accSet \cup denySet
                  PROVE  TerminalProjection(accSet \cup {e}, denySet) =
                           [x \in accSet \cup denySet \cup {e} |->
                             IF x = e
                             THEN TerminalCell(e, "ALLOW")
                             ELSE TerminalProjection(accSet, denySet)[x]]
    OBVIOUS
  <1>2. DOMAIN TerminalProjection(accSet \cup {e}, denySet) =
          accSet \cup denySet \cup {e}
    BY TerminalProjectionDomain
  <1>3. DOMAIN [x \in accSet \cup denySet \cup {e} |->
                  IF x = e
                  THEN TerminalCell(e, "ALLOW")
                  ELSE TerminalProjection(accSet, denySet)[x]] =
          accSet \cup denySet \cup {e}
    OBVIOUS
  <1>4. \A x \in accSet \cup denySet \cup {e} :
          TerminalProjection(accSet \cup {e}, denySet)[x] =
            IF x = e
            THEN TerminalCell(e, "ALLOW")
            ELSE TerminalProjection(accSet, denySet)[x]
    <2>1. SUFFICES ASSUME NEW x \in accSet \cup denySet \cup {e}
                    PROVE  TerminalProjection(accSet \cup {e}, denySet)[x] =
                             IF x = e
                             THEN TerminalCell(e, "ALLOW")
                             ELSE TerminalProjection(accSet, denySet)[x]
      OBVIOUS
    <2>2. CASE x = e
      <3>1. QED
        BY <1>1, <2>2, SMT
           DEF TerminalProjection, TerminalCell
    <2>3. CASE x # e
      <3>1. QED
        BY <1>1, <2>1, <2>3, SMT
           DEF TerminalProjection, TerminalCell
    <2>4. QED
      BY <2>2, <2>3
  <1>5. QED
    BY <1>2, <1>3, <1>4, Force
       DEF TerminalProjection, TerminalCell


THEOREM TerminalProjectionAppendBlock ==
  \A accSet, denySet, e :
    e \notin accSet \cup denySet =>
      TerminalProjection(accSet, denySet \cup {e}) =
        [x \in accSet \cup denySet \cup {e} |->
          IF x = e
          THEN TerminalCell(e, "BLOCK")
          ELSE TerminalProjection(accSet, denySet)[x]]
PROOF
  <1>1. SUFFICES ASSUME NEW accSet, NEW denySet, NEW e,
                          e \notin accSet \cup denySet
                  PROVE  TerminalProjection(accSet, denySet \cup {e}) =
                           [x \in accSet \cup denySet \cup {e} |->
                             IF x = e
                             THEN TerminalCell(e, "BLOCK")
                             ELSE TerminalProjection(accSet, denySet)[x]]
    OBVIOUS
  <1>2. DOMAIN TerminalProjection(accSet, denySet \cup {e}) =
          accSet \cup denySet \cup {e}
    BY TerminalProjectionDomain
  <1>3. DOMAIN [x \in accSet \cup denySet \cup {e} |->
                  IF x = e
                  THEN TerminalCell(e, "BLOCK")
                  ELSE TerminalProjection(accSet, denySet)[x]] =
          accSet \cup denySet \cup {e}
    OBVIOUS
  <1>4. \A x \in accSet \cup denySet \cup {e} :
          TerminalProjection(accSet, denySet \cup {e})[x] =
            IF x = e
            THEN TerminalCell(e, "BLOCK")
            ELSE TerminalProjection(accSet, denySet)[x]
    <2>1. SUFFICES ASSUME NEW x \in accSet \cup denySet \cup {e}
                    PROVE  TerminalProjection(accSet, denySet \cup {e})[x] =
                             IF x = e
                             THEN TerminalCell(e, "BLOCK")
                             ELSE TerminalProjection(accSet, denySet)[x]
      OBVIOUS
    <2>2. CASE x = e
      <3>1. QED
        BY <1>1, <2>2, SMT
           DEF TerminalProjection, TerminalCell
    <2>3. CASE x # e
      <3>1. QED
        BY <1>1, <2>1, <2>3, SMT
           DEF TerminalProjection, TerminalCell
    <2>4. QED
      BY <2>2, <2>3
  <1>5. QED
    BY <1>2, <1>3, <1>4, AllIsa
       DEF TerminalProjection


THEOREM ExportUniverseTyping ==
  \A e \in ExportUniverse :
    /\ e.source \in Contexts
    /\ e.target \in Contexts
    /\ e.artifact \in Artifacts
PROOF
  BY SimplifyAndSolve DEF ExportUniverse


THEOREM ExportBridgeTyping ==
  \A e \in ExportUniverse :
    /\ BridgeBinding(e) \in BridgeBindings
    /\ e.target \in Contexts
    /\ <<e.target, BridgeBinding(e)>>
         \in BridgeRecognizedAuthorityBindings
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse
                  PROVE  /\ BridgeBinding(e) \in BridgeBindings
                         /\ e.target \in Contexts
                         /\ <<e.target, BridgeBinding(e)>>
                              \in BridgeRecognizedAuthorityBindings
    OBVIOUS
  <1>2. /\ e.target \in Contexts
         /\ e.artifact \in Artifacts
    BY <1>1, ExportUniverseTyping
  <1>3. BridgeBinding(e) = <<e.target, e.artifact>>
    BY DEF BridgeBinding
  <1>4. BridgeBinding(e) \in BridgeBindings
    BY <1>2, <1>3 DEF BridgeBindings
  <1>5. <<e.target, BridgeBinding(e)>> \in Contexts \X BridgeBindings
    BY <1>2, <1>4
  <1>6. <<e.target, BridgeBinding(e)>>[1] =
           <<e.target, BridgeBinding(e)>>[2][1]
    BY <1>3, SimplifyAndSolve
  <1>7. <<e.target, BridgeBinding(e)>>
           \in BridgeRecognizedAuthorityBindings
    BY <1>5, <1>6, SimplifyAndSolve
       DEF BridgeRecognizedAuthorityBindings
  <1>8. QED
    BY <1>2, <1>4, <1>7


THEOREM NetworkInitRefinesSeedInit ==
  Init => Seed!Init
PROOF
  BY DEF Init,
         Seed!Init,
         ProjectedRequestMeta,
         ProjectedTerminalMeta,
         ProjectedConflicts,
         RequestProjection,
         TerminalProjection


THEOREM ObserveProjectionStep ==
  \A e \in ExportUniverse :
    Observe(e) =>
      /\ ProjectedRequestMeta' =
           [x \in DOMAIN ProjectedRequestMeta \cup {e} |->
             IF x = e
             THEN RequestCell(e)
             ELSE ProjectedRequestMeta[x]]
      /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, Observe(e)
                  PROVE  /\ ProjectedRequestMeta' =
                              [x \in DOMAIN ProjectedRequestMeta \cup {e} |->
                                IF x = e
                                THEN RequestCell(e)
                                ELSE ProjectedRequestMeta[x]]
                         /\ UNCHANGED
                              <<ProjectedTerminalMeta, ProjectedConflicts>>
    OBVIOUS
  <1>2. /\ imports' = imports \cup {e}
         /\ e \notin imports
    BY <1>1 DEF Observe
  <1>3. /\ accepted' = accepted
         /\ denied' = denied
    BY <1>1 DEF Observe
  <1>4. DOMAIN ProjectedRequestMeta = imports
    BY RequestProjectionDomain DEF ProjectedRequestMeta
  <1>5. QED
    BY <1>2, <1>3, <1>4, SMT
       DEF ProjectedRequestMeta,
           ProjectedTerminalMeta,
           ProjectedConflicts,
           RequestProjection,
           TerminalProjection,
           RequestCell


THEOREM ResolveAcceptProjectionStep ==
  \A e \in ExportUniverse :
    ResolveAccept(e) =>
      /\ ProjectedTerminalMeta' =
           [x \in DOMAIN ProjectedTerminalMeta \cup {e} |->
             IF x = e
             THEN TerminalCell(e, "ALLOW")
             ELSE ProjectedTerminalMeta[x]]
      /\ UNCHANGED <<ProjectedRequestMeta, ProjectedConflicts>>
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveAccept(e)
                  PROVE  /\ ProjectedTerminalMeta' =
                              [x \in DOMAIN ProjectedTerminalMeta \cup {e} |->
                                IF x = e
                                THEN TerminalCell(e, "ALLOW")
                                ELSE ProjectedTerminalMeta[x]]
                         /\ UNCHANGED
                              <<ProjectedRequestMeta, ProjectedConflicts>>
    OBVIOUS
  <1>2. /\ accepted' = accepted \cup {e}
         /\ e \notin accepted \cup denied
    BY <1>1 DEF ResolveAccept
  <1>3. /\ imports' = imports
         /\ denied' = denied
    BY <1>1 DEF ResolveAccept
  <1>4. DOMAIN ProjectedTerminalMeta = accepted \cup denied
    BY TerminalProjectionDomain DEF ProjectedTerminalMeta
  <1>5. ProjectedTerminalMeta' =
          TerminalProjection(accepted \cup {e}, denied)
    BY <1>2, <1>3 DEF ProjectedTerminalMeta
  <1>6. TerminalProjection(accepted \cup {e}, denied) =
          [x \in accepted \cup denied \cup {e} |->
            IF x = e
            THEN TerminalCell(e, "ALLOW")
            ELSE TerminalProjection(accepted, denied)[x]]
    BY <1>2, TerminalProjectionAppendAllow
  <1>7. QED
    BY <1>3, <1>4, <1>5, <1>6
       DEF ProjectedRequestMeta,
           ProjectedTerminalMeta,
           ProjectedConflicts


THEOREM ResolveDenyProjectionStep ==
  \A e \in ExportUniverse :
    ResolveDeny(e) =>
      /\ ProjectedTerminalMeta' =
           [x \in DOMAIN ProjectedTerminalMeta \cup {e} |->
             IF x = e
             THEN TerminalCell(e, "BLOCK")
             ELSE ProjectedTerminalMeta[x]]
      /\ UNCHANGED <<ProjectedRequestMeta, ProjectedConflicts>>
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveDeny(e)
                  PROVE  /\ ProjectedTerminalMeta' =
                              [x \in DOMAIN ProjectedTerminalMeta \cup {e} |->
                                IF x = e
                                THEN TerminalCell(e, "BLOCK")
                                ELSE ProjectedTerminalMeta[x]]
                         /\ UNCHANGED
                              <<ProjectedRequestMeta, ProjectedConflicts>>
    OBVIOUS
  <1>2. /\ denied' = denied \cup {e}
         /\ e \notin accepted \cup denied
    BY <1>1 DEF ResolveDeny
  <1>3. /\ imports' = imports
         /\ accepted' = accepted
    BY <1>1 DEF ResolveDeny
  <1>4. DOMAIN ProjectedTerminalMeta = accepted \cup denied
    BY TerminalProjectionDomain DEF ProjectedTerminalMeta
  <1>5. ProjectedTerminalMeta' =
          TerminalProjection(accepted, denied \cup {e})
    BY <1>2, <1>3 DEF ProjectedTerminalMeta
  <1>6. TerminalProjection(accepted, denied \cup {e}) =
          [x \in accepted \cup denied \cup {e} |->
            IF x = e
            THEN TerminalCell(e, "BLOCK")
            ELSE TerminalProjection(accepted, denied)[x]]
    BY <1>2, TerminalProjectionAppendBlock
  <1>7. QED
    BY <1>3, <1>4, <1>5, <1>6
       DEF ProjectedRequestMeta,
           ProjectedTerminalMeta,
           ProjectedConflicts


THEOREM ObserveRefinesSeedRegisterRequest ==
  \A e \in ExportUniverse :
    Observe(e) => BridgeObserveAsSeedRegister(e)
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, Observe(e)
                  PROVE BridgeObserveAsSeedRegister(e)
    OBVIOUS
  <1>2. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
         /\ <<e.target, BridgeBinding(e)>>
              \in BridgeRecognizedAuthorityBindings
    BY <1>1, ExportBridgeTyping
  <1>3. e \notin Seed!Requests
    BY <1>1, RequestProjectionDomain
       DEF Observe, Seed!Requests, ProjectedRequestMeta
  <1>4. /\ ProjectedRequestMeta' =
              [x \in Seed!Requests \cup {e} |->
                IF x = e
                THEN [binding |-> BridgeBinding(e),
                      previous |-> NoCommitmentValue]
                ELSE ProjectedRequestMeta[x]]
         /\ UNCHANGED <<ProjectedTerminalMeta, ProjectedConflicts>>
    BY <1>1, ObserveProjectionStep
       DEF Seed!Requests, RequestCell
  <1>5. e \in ExportUniverse \ Seed!Requests
    BY <1>1, <1>3
  <1>6. NoCommitmentValue = NoCommitmentValue \/ NoCommitmentValue \in {}
    OBVIOUS
  <1>7. QED
    BY <1>2, <1>4, <1>5, <1>6
       DEF BridgeObserveAsSeedRegister,
           Seed!RegisterRequest


THEOREM ResolveAcceptRefinesSeedSubmitAllow ==
  \A e \in ExportUniverse :
    ResolveAccept(e) => BridgeAcceptAsSeedSubmit(e)
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveAccept(e)
                  PROVE BridgeAcceptAsSeedSubmit(e)
    OBVIOUS
  <1>2. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
         /\ <<e.target, BridgeBinding(e)>>
              \in BridgeRecognizedAuthorityBindings
    BY <1>1, ExportBridgeTyping
  <1>3. e \in Seed!Requests
    BY <1>1, RequestProjectionDomain
       DEF ResolveAccept, Seed!Requests, ProjectedRequestMeta
  <1>4. e \notin Seed!TerminalRequests
    BY <1>1, TerminalProjectionDomain
       DEF ResolveAccept, Seed!TerminalRequests, ProjectedTerminalMeta
  <1>5. e \notin ProjectedConflicts
    BY DEF ProjectedConflicts
  <1>6. Seed!RequestBinding(e) = BridgeBinding(e)
    BY <1>1
       DEF ResolveAccept,
           Seed!RequestBinding,
           ProjectedRequestMeta,
           RequestProjection,
           RequestCell
  <1>7. /\ ProjectedTerminalMeta' =
              [x \in Seed!TerminalRequests \cup {e} |->
                IF x = e
                THEN [resolution |-> "ALLOW", authority |-> e.target]
                ELSE ProjectedTerminalMeta[x]]
         /\ UNCHANGED <<ProjectedRequestMeta, ProjectedConflicts>>
    BY <1>1, ResolveAcceptProjectionStep
       DEF Seed!TerminalRequests, TerminalCell
  <1>8. QED
    BY <1>2, <1>3, <1>4, <1>5, <1>6, <1>7
       DEF BridgeAcceptAsSeedSubmit,
           Seed!SubmitResolution,
           Seed!TerminalResolutions


THEOREM ResolveDenyRefinesSeedSubmitBlock ==
  \A e \in ExportUniverse :
    ResolveDeny(e) => BridgeDenyAsSeedSubmit(e)
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveDeny(e)
                  PROVE BridgeDenyAsSeedSubmit(e)
    OBVIOUS
  <1>2. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
         /\ <<e.target, BridgeBinding(e)>>
              \in BridgeRecognizedAuthorityBindings
    BY <1>1, ExportBridgeTyping
  <1>3. e \in Seed!Requests
    BY <1>1, RequestProjectionDomain
       DEF ResolveDeny, Seed!Requests, ProjectedRequestMeta
  <1>4. e \notin Seed!TerminalRequests
    BY <1>1, TerminalProjectionDomain
       DEF ResolveDeny, Seed!TerminalRequests, ProjectedTerminalMeta
  <1>5. e \notin ProjectedConflicts
    BY DEF ProjectedConflicts
  <1>6. Seed!RequestBinding(e) = BridgeBinding(e)
    BY <1>1
       DEF ResolveDeny,
           Seed!RequestBinding,
           ProjectedRequestMeta,
           RequestProjection,
           RequestCell
  <1>7. /\ ProjectedTerminalMeta' =
              [x \in Seed!TerminalRequests \cup {e} |->
                IF x = e
                THEN [resolution |-> "BLOCK", authority |-> e.target]
                ELSE ProjectedTerminalMeta[x]]
         /\ UNCHANGED <<ProjectedRequestMeta, ProjectedConflicts>>
    BY <1>1, ResolveDenyProjectionStep
       DEF Seed!TerminalRequests, TerminalCell
  <1>8. QED
    BY <1>2, <1>3, <1>4, <1>5, <1>6, <1>7
       DEF BridgeDenyAsSeedSubmit,
           Seed!SubmitResolution,
           Seed!TerminalResolutions


THEOREM NetworkOnlyActionsStutterAtSeedBoundary ==
  NetworkOnlyAction => UNCHANGED ProjectedSeedVars
PROOF
  BY DEF NetworkOnlyAction,
         Join,
         GrantRoute,
         ExportArtifact,
         Deliver,
         SuspendRoute,
         Withdraw,
         ProjectedSeedVars,
         ProjectedRequestMeta,
         ProjectedTerminalMeta,
         ProjectedConflicts,
         RequestProjection,
         TerminalProjection


THEOREM ObserveRefinesSeedRecognizedTransition ==
  \A e \in ExportUniverse :
    Observe(e) => Seed!RecognizedSeedTransition
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, Observe(e)
                  PROVE  Seed!RecognizedSeedTransition
    OBVIOUS
  <1>2. BridgeObserveAsSeedRegister(e)
    BY <1>1, ObserveRefinesSeedRegisterRequest
  <1>3. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
    BY <1>1, ExportBridgeTyping
  <1>4. NoCommitmentValue \in {} \cup {NoCommitmentValue}
    OBVIOUS
  <1>5. QED
    BY <1>1, <1>2, <1>3, <1>4
       DEF Seed!RecognizedSeedTransition,
           BridgeObserveAsSeedRegister


THEOREM ResolveAcceptRefinesSeedRecognizedTransition ==
  \A e \in ExportUniverse :
    ResolveAccept(e) => Seed!RecognizedSeedTransition
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveAccept(e)
                  PROVE  Seed!RecognizedSeedTransition
    OBVIOUS
  <1>2. BridgeAcceptAsSeedSubmit(e)
    BY <1>1, ResolveAcceptRefinesSeedSubmitAllow
  <1>3. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
    BY <1>1, ExportBridgeTyping
  <1>4. "ALLOW" \in Seed!TerminalResolutions
    BY DEF Seed!TerminalResolutions
  <1>5. QED
    BY <1>1, <1>2, <1>3, <1>4
       DEF Seed!RecognizedSeedTransition,
           BridgeAcceptAsSeedSubmit


THEOREM ResolveDenyRefinesSeedRecognizedTransition ==
  \A e \in ExportUniverse :
    ResolveDeny(e) => Seed!RecognizedSeedTransition
PROOF
  <1>1. SUFFICES ASSUME NEW e \in ExportUniverse, ResolveDeny(e)
                  PROVE  Seed!RecognizedSeedTransition
    OBVIOUS
  <1>2. BridgeDenyAsSeedSubmit(e)
    BY <1>1, ResolveDenyRefinesSeedSubmitBlock
  <1>3. /\ BridgeBinding(e) \in BridgeBindings
         /\ e.target \in Contexts
    BY <1>1, ExportBridgeTyping
  <1>4. "BLOCK" \in Seed!TerminalResolutions
    BY DEF Seed!TerminalResolutions
  <1>5. QED
    BY <1>1, <1>2, <1>3, <1>4
       DEF Seed!RecognizedSeedTransition,
           BridgeDenyAsSeedSubmit


THEOREM ResolveRefinesSeedRecognizedTransition ==
  \A e \in ExportUniverse :
    Resolve(e) => Seed!RecognizedSeedTransition
PROOF
  BY ResolveAcceptRefinesSeedRecognizedTransition,
     ResolveDenyRefinesSeedRecognizedTransition
     DEF Resolve


THEOREM NetworkActionDecomposesAtSeedBoundary ==
  NetworkAction =>
    \/ NetworkOnlyAction
    \/ \E e \in ExportUniverse : Observe(e)
    \/ \E e \in ExportUniverse : Resolve(e)
PROOF
  BY DEF NetworkAction, NetworkOnlyAction


THEOREM NetworkActionRefinesSeedStep ==
  NetworkAction => Seed!Next \/ UNCHANGED ProjectedSeedVars
PROOF
  <1>1. SUFFICES ASSUME NetworkAction
                  PROVE  Seed!Next \/ UNCHANGED ProjectedSeedVars
    OBVIOUS
  <1>2. \/ NetworkOnlyAction
         \/ \E e \in ExportUniverse : Observe(e)
         \/ \E e \in ExportUniverse : Resolve(e)
    BY <1>1, NetworkActionDecomposesAtSeedBoundary
  <1>3. CASE NetworkOnlyAction
    <2>1. QED
      BY <1>3, NetworkOnlyActionsStutterAtSeedBoundary
  <1>4. CASE \E e \in ExportUniverse : Observe(e)
    <2>1. Seed!RecognizedSeedTransition
      BY <1>4, ObserveRefinesSeedRecognizedTransition
    <2>2. QED
      BY <2>1 DEF Seed!Next
  <1>5. CASE \E e \in ExportUniverse : Resolve(e)
    <2>1. Seed!RecognizedSeedTransition
      BY <1>5, ResolveRefinesSeedRecognizedTransition
    <2>2. QED
      BY <2>1 DEF Seed!Next
  <1>6. QED
    BY <1>2, <1>3, <1>4, <1>5


THEOREM NetworkStateStutterRefinesSeedStutter ==
  UNCHANGED vars => UNCHANGED ProjectedSeedVars
PROOF
  BY DEF vars,
         ProjectedSeedVars,
         ProjectedRequestMeta,
         ProjectedTerminalMeta,
         ProjectedConflicts,
         RequestProjection,
         TerminalProjection


THEOREM NetworkBoxStepRefinesSeedBoxStep ==
  [NetworkAction]_vars => [Seed!Next]_ProjectedSeedVars
PROOF
  BY NetworkActionRefinesSeedStep,
     NetworkStateStutterRefinesSeedStutter
     DEF vars, ProjectedSeedVars


THEOREM NetworkBoxStepRefinesSeedSpecBoxStep ==
  [NetworkAction]_vars => [Seed!Next]_Seed!vars
PROOF
  BY NetworkBoxStepRefinesSeedBoxStep
     DEF Seed!vars, ProjectedSeedVars


THEOREM NetworkSafetyRefinesSeedResolution ==
  SafetySpec => Seed!Spec
PROOF
  BY PTL,
     NetworkInitRefinesSeedInit,
     NetworkBoxStepRefinesSeedSpecBoxStep
     DEF SafetySpec, Seed!Spec


THEOREM NetworkEvaluatorMatchesSeedResolution ==
  TerminalRecognitionDisjoint =>
    \A e \in ExportUniverse :
      /\ ProjectedSeedResolution(e) = NetworkProjectedSeedResolution(e)
      /\ ProjectedSeedEffectPermitted(e) = NetworkProjectedSeedEffectPermitted(e)
PROOF
  BY DEF TerminalRecognitionDisjoint,
         ProjectedSeedResolution,
         ProjectedSeedEffectPermitted,
         NetworkProjectedSeedResolution,
         NetworkProjectedSeedEffectPermitted,
         Seed!ResolutionOf,
         Seed!EffectPermitted,
         Seed!Requests,
         Seed!TerminalRequests,
         Seed!TerminalResolution,
         ProjectedRequestMeta,
         ProjectedTerminalMeta,
         ProjectedConflicts,
         RequestProjection,
         TerminalProjection,
         TerminalCell

=============================================================================
