------------------- MODULE LivenessBoundaryProofs -------------------
EXTENDS LivenessContract, TLAPS

THEOREM LivenessAddsNoState == LivenessStateAdded = {}
PROOF
  BY DEF LivenessStateAdded

THEOREM LivenessAddsNoTransitions == LivenessTransitionsAdded = {}
PROOF
  BY DEF LivenessTransitionsAdded

THEOREM LivenessDoesNotRequireAllow == ResolvedResultPermitted("BLOCK")
PROOF
  BY DEF ResolvedResultPermitted, SeedTerminalResults

THEOREM LivenessPreservesOwnershipBoundary ==
  /\ LivenessAddsNoState
  /\ LivenessAddsNoTransitions
  /\ LivenessDoesNotRequireAllow
PROOF
  BY LivenessAddsNoState, LivenessAddsNoTransitions, LivenessDoesNotRequireAllow

=============================================================================
