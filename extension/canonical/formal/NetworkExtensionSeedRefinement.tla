---------------- MODULE NetworkExtensionSeedRefinement ----------------
EXTENDS NetworkExtension

(***************************************************************************
Exact refinement mapping from the Network Extension assurance state into the
pinned ASET SeedResolution state shape.

SeedResolution.tla itself is NOT vendored into this repository.  TLAPS loads
the exact upstream module from a separately supplied include directory and
the runner verifies its SHA-256 against the pinned Seed release before proof.

The mapping is intentionally narrow:
- each target-local imported export is one Seed ResolutionId;
- the target-scoped pair <<target Context, exported artifact>> is the opaque
  Seed Binding, preventing cross-Context Binding aliasing in the projection;
- the target Context is the abstract local Seed Authority identity;
- Observe corresponds to RegisterRequest with no previous commitment;
- ResolveAccept corresponds to terminal ALLOW;
- ResolveDeny corresponds to terminal BLOCK;
- all other Network-only actions stutter with respect to Seed state;
- the network projection introduces no Seed conflict observation.

The target Context -> Authority and target/artifact -> Binding identifications
are formal abstraction mappings only. They do not assert that concrete Context
IDs are concrete Authority IDs or that protocol values are concrete Seed
Bindings.
***************************************************************************)

NoCommitmentValue == "NETWORK-NO-COMMITMENT"

BridgeBindings == Contexts \X Artifacts
BridgeBinding(e) == <<e.target, e.artifact>>

(*
Equivalent proof-friendly form of
  {<<c, <<c, a>>>> : c \in Contexts, a \in Artifacts}.
The filter keeps recognition target-local without requiring TLAPS to invert a
tuple-valued replacement-set constructor.
*)
BridgeRecognizedAuthorityBindings ==
  {p \in Contexts \X BridgeBindings : p[1] = p[2][1]}

(***************************************************************************
Pure projection constructors.  Keeping these operators independent of primed
state lets the TLAPS proof separate ordinary function algebra from action
simulation.  They do not change the refinement mapping.
***************************************************************************)
RequestCell(e) ==
  [binding |-> BridgeBinding(e),
   previous |-> NoCommitmentValue]

TerminalCell(e, value) ==
  [resolution |-> value,
   authority |-> e.target]

RequestProjection(S) ==
  [e \in S |-> RequestCell(e)]

TerminalProjection(A, D) ==
  [e \in A \cup D |->
    IF e \in A
    THEN TerminalCell(e, "ALLOW")
    ELSE TerminalCell(e, "BLOCK")]

ProjectedRequestMeta == RequestProjection(imports)
ProjectedTerminalMeta == TerminalProjection(accepted, denied)

ProjectedConflicts == {}

ProjectedSeedVars ==
  <<ProjectedRequestMeta, ProjectedTerminalMeta, ProjectedConflicts>>

Seed == INSTANCE SeedResolution
  WITH ResolutionIds <- ExportUniverse,
       Bindings <- BridgeBindings,
       Authorities <- Contexts,
       TerminalCommitments <- {},
       RecognizedTerminalCommitments <- {},
       NoCommitment <- NoCommitmentValue,
       RecognizedAuthorityBindings <- BridgeRecognizedAuthorityBindings,
       requestMeta <- ProjectedRequestMeta,
       terminalMeta <- ProjectedTerminalMeta,
       conflicts <- ProjectedConflicts

BridgeObserveAsSeedRegister(e) ==
  Seed!RegisterRequest(e, BridgeBinding(e), e.target, NoCommitmentValue)

BridgeAcceptAsSeedSubmit(e) ==
  Seed!SubmitResolution(e, BridgeBinding(e), e.target, "ALLOW")

BridgeDenyAsSeedSubmit(e) ==
  Seed!SubmitResolution(e, BridgeBinding(e), e.target, "BLOCK")

NetworkOnlyAction ==
  \/ \E c \in Contexts : Join(c)
  \/ \E s \in Contexts, t \in Contexts : GrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ExportArtifact(s, t, a)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E s \in Contexts, t \in Contexts : SuspendRoute(s, t)
  \/ \E c \in Contexts : Withdraw(c)

ProjectedSeedResolution(e) == Seed!ResolutionOf(e)
ProjectedSeedEffectPermitted(e) == Seed!EffectPermitted(e)

NetworkProjectedSeedResolution(e) ==
  IF e \notin imports
  THEN "UNKNOWN"
  ELSE IF e \in accepted
       THEN "ALLOW"
       ELSE IF e \in denied
            THEN "BLOCK"
            ELSE "UNKNOWN"

NetworkProjectedSeedEffectPermitted(e) ==
  NetworkProjectedSeedResolution(e) = "ALLOW"

BridgeProjectionWellFormed ==
  /\ DOMAIN ProjectedRequestMeta = imports
  /\ DOMAIN ProjectedTerminalMeta = accepted \cup denied
  /\ ProjectedConflicts = {}

=============================================================================
