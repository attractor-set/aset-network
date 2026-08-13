-------------- MODULE OperationalRelationalPairingProofs --------------
EXTENDS RestrictedOperationalSemantics, TLAPS

THEOREM AdmitFreshPairing ==
  \A s, t, o, result : OperationalAdmitFresh(s, t, o, result) <=> AdmitFresh(s, t, o, result)
PROOF
  BY DEF OperationalAdmitFresh, AdmitFresh, FreshIdentifier, SameIdentifier, StateType

THEOREM AdmitReplayPairing ==
  \A s, t, o, result : OperationalAdmitReplay(s, t, o, result) <=> AdmitReplay(s, t, o, result)
PROOF
  BY DEF OperationalAdmitReplay, AdmitReplay, ExactReplay, StateType

THEOREM RejectConflictPairing ==
  \A s, t, o, result : OperationalRejectConflict(s, t, o, result) <=> RejectConflict(s, t, o, result)
PROOF
  BY DEF OperationalRejectConflict,
         RejectConflict,
         ConflictingIdentifier,
         SameIdentifier,
         StateType

THEOREM OperationalRelationalPairing ==
  /\ AdmitFreshPairing
  /\ AdmitReplayPairing
  /\ RejectConflictPairing
PROOF
  BY AdmitFreshPairing, AdmitReplayPairing, RejectConflictPairing

=============================================================================
