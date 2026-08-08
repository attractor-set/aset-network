--------------------------- MODULE NetworkHistory ---------------------------
EXTENDS Naturals, Sequences, FiniteSets

(***************************************************************************
Bounded trace assurance projection for NET-INV-010.

The main NetworkExtension TLC state intentionally omits execution history so
permutations that reach the same semantic state are deduplicated.  This small
independent model checks the history-specific obligation: every accepted
transition appends exactly one fresh history digest and prior history is never
rewritten.

HistoryDigests are opaque identities.  This module does not model digest
construction or cryptographic collision resistance.
***************************************************************************)

CONSTANTS HistoryDigests

ASSUME HistoryDigests # {}

VARIABLES history, acceptedDigests

vars == <<history, acceptedDigests>>

Init ==
  /\ history = <<>>
  /\ acceptedDigests = {}

AcceptTransition(d) ==
  /\ d \in HistoryDigests \ acceptedDigests
  /\ acceptedDigests' = acceptedDigests \cup {d}
  /\ history' = Append(history, d)

HistoryAction ==
  \E d \in HistoryDigests : AcceptTransition(d)

HistorySpec == Init /\ [][HistoryAction]_vars

HistorySet ==
  {history[i] : i \in 1..Len(history)}

Prefix(s, t) ==
  /\ Len(s) <= Len(t)
  /\ \A i \in 1..Len(s) : s[i] = t[i]

TypeOK ==
  /\ history \in Seq(HistoryDigests)
  /\ acceptedDigests \subseteq HistoryDigests

HistoryExactlyTracksAccepted ==
  /\ HistorySet = acceptedDigests
  /\ Len(history) = Cardinality(acceptedDigests)

NoDuplicateHistoryDigests ==
  Len(history) = Cardinality(HistorySet)

HistoryTerminal == acceptedDigests = HistoryDigests

NoUnexpectedHistoryDeadlock ==
  HistoryTerminal \/ ENABLED HistoryAction

HistoryPrefixPreserved ==
  [][Prefix(history, history')]_vars

AcceptedTransitionAppendsExactlyOne ==
  [][acceptedDigests' # acceptedDigests
      => /\ Len(history') = Len(history) + 1
         /\ Prefix(history, history')
         /\ acceptedDigests' = acceptedDigests \cup {history'[Len(history')]}
    ]_vars

=============================================================================
