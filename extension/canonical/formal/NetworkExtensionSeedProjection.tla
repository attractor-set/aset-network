---------------- MODULE NetworkExtensionSeedProjection ----------------
EXTENDS NetworkExtension

ContextImports(c) == {o \in imports : o.target = c}
ProjectedSeedStatus(o) == IF o \in imports THEN "UNKNOWN" ELSE "NOT_APPLICABLE"
ProjectedSeedEnforcement(o) == IF o \in imports THEN "BLOCKED" ELSE "NOT_APPLICABLE"

PerContextSeedProjectionContract ==
  \A c \in Contexts, o \in ContextImports(c) :
    /\ ProjectedSeedStatus(o) = "UNKNOWN"
    /\ ProjectedSeedEnforcement(o) = "BLOCKED"

=============================================================================
