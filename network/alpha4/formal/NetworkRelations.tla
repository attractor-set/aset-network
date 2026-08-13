-------------------------- MODULE NetworkRelations --------------------------
EXTENDS FiniteSets

CONSTANTS ImportIDs, Sources, Targets, EvidenceDigests

ASSUME /\ ImportIDs # {}
       /\ Sources # {}
       /\ Targets # {}
       /\ EvidenceDigests # {}

ObservationUniverse ==
  [import_id : ImportIDs,
   source_context : Sources,
   target_context : Targets,
   evidence_digest : EvidenceDigests]

StateType == SUBSET ObservationUniverse
ResultCodes == {"IMPORT_ADMITTED", "IDEMPOTENT_REPLAY", "IDENTIFIER_CONFLICT"}

SameIdentifier(s, o) == {x \in s : x.import_id = o.import_id}
FreshIdentifier(s, o) == SameIdentifier(s, o) = {}
ExactReplay(s, o) == o \in s
ConflictingIdentifier(s, o) == /\ SameIdentifier(s, o) # {} /\ o \notin s

AdmitFresh(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ FreshIdentifier(s, o)
  /\ t = s \cup {o}
  /\ result = "IMPORT_ADMITTED"

AdmitReplay(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ ExactReplay(s, o)
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

RejectConflict(s, t, o, result) ==
  /\ s \in StateType
  /\ o \in ObservationUniverse
  /\ ConflictingIdentifier(s, o)
  /\ t = s
  /\ result = "IDENTIFIER_CONFLICT"

AdmitImport(s, t, o, result) ==
  \/ AdmitFresh(s, t, o, result)
  \/ AdmitReplay(s, t, o, result)
  \/ RejectConflict(s, t, o, result)

AcceptedResult(result) == result \in {"IMPORT_ADMITTED", "IDEMPOTENT_REPLAY"}
SeedProjectionRecognition(result) == IF AcceptedResult(result) THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
SeedProjectionEffectPermitted(result) == FALSE

=============================================================================
