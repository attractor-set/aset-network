------------------------ MODULE NetworkExtensionTLC ------------------------
EXTENDS NetworkExtension

(***************************************************************************
Bounded TLC harness for the normative minimal admission model.

NetworkExtension.ImportsAppendOnly is intentionally an action predicate:
    imports \subseteq imports'
TLC PROPERTIES entries must name temporal formulas.  This harness lifts the
action predicate to a stuttering-closed temporal property without changing
the normative NetworkExtension state machine or TLAPS proof target.
***************************************************************************)

ImportsAppendOnlyTemporal == [][ImportsAppendOnly]_vars

=============================================================================
