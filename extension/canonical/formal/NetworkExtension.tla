-------------------------- MODULE NetworkExtension --------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT Contexts
VARIABLES members, routes, imported, recognized

vars == <<members, routes, imported, recognized>>

Init == /\ members = {}
        /\ routes = {}
        /\ imported = {}
        /\ recognized = {}

Join(c) == /\ c \in Contexts
           /\ c \notin members
           /\ members' = members \cup {c}
           /\ UNCHANGED <<routes, imported, recognized>>

Observe(i) == /\ i \notin imported
              /\ imported' = imported \cup {i}
              /\ UNCHANGED <<members, routes, recognized>>

Recognize(i) == /\ i \in imported
                /\ i \notin recognized
                /\ recognized' = recognized \cup {i}
                /\ UNCHANGED <<members, routes, imported>>

Next == (\E c \in Contexts: Join(c)) \/ (\E i \in Contexts: Observe(i)) \/ (\E i \in Contexts: Recognize(i))

RecognitionRequiresImport == recognized \subseteq imported

Spec == Init /\ [][Next]_vars
=============================================================================
