---------------- MODULE RestrictedOperationalSemantics ----------------
EXTENDS NetworkRelations

OperationalAdmitFresh(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ SameIdentifier(s, o) = {}
  /\ t = s \cup {o}
  /\ result = "IMPORT_ADMITTED"

OperationalAdmitReplay(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ o \in s
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

OperationalRejectConflict(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ SameIdentifier(s, o) # {}
  /\ o \notin s
  /\ t = s
  /\ result = "IDENTIFIER_CONFLICT"

=============================================================================
