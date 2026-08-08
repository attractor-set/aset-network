------------------- MODULE NetworkExtensionSeedProjection -------------------
EXTENDS NetworkExtension

(***************************************************************************
Per-Context projection boundary toward the pinned ASET Seed resolution
algebra. This module deliberately does not copy or redefine SeedResolution.
It exposes the observable projection that a later TLAPS refinement bridge
must instantiate against the exact pinned Seed module.
***************************************************************************)

SeedUnknown == "UNKNOWN"
SeedAccept == "ACCEPT"
SeedDeny == "DENY"
SeedBlocked == "BLOCKED"
SeedAllow == "ALLOW"

ProjectedStatus(c, e) ==
  IF e \notin ContextImports(c)
  THEN "NOT_APPLICABLE"
  ELSE IF e \in ContextAccepted(c)
       THEN SeedAccept
       ELSE IF e \in ContextDenied(c)
            THEN SeedDeny
            ELSE SeedUnknown

ProjectedEnforcement(c, e) ==
  IF e \notin ContextImports(c)
  THEN "NOT_APPLICABLE"
  ELSE IF e \in ContextAccepted(c)
       THEN SeedAllow
       ELSE SeedBlocked

ProjectionFailClosed ==
  \A c \in Contexts, e \in ExportUniverse :
    ProjectedStatus(c, e) \in {SeedUnknown, SeedDeny}
      => ProjectedEnforcement(c, e) = SeedBlocked

ProjectionAllowRequiresLocalAccept ==
  \A c \in Contexts, e \in ExportUniverse :
    ProjectedEnforcement(c, e) = SeedAllow
      => /\ e \in ContextAccepted(c)
         /\ ProjectedStatus(c, e) = SeedAccept

ProjectionNeverTransfersAuthority == LocalAuthoritySovereignty

PerContextSeedProjectionContract ==
  /\ PerContextSeedProjectionWellFormed
  /\ ProjectionFailClosed
  /\ ProjectionAllowRequiresLocalAccept
  /\ ProjectionNeverTransfersAuthority

=============================================================================
