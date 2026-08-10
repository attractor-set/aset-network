---------------- MODULE NetworkLegacyAdmissionRefinement ----------------
EXTENDS NetworkLegacyAlpha2

Core == INSTANCE NetworkExtension
  WITH Contexts <- Contexts,
       Artifacts <- Artifacts,
       imports <- imports

LegacyNonAdmissionAction ==
  \/ \E c \in Contexts : Join(c)
  \/ \E s \in Contexts, t \in Contexts : GrantRoute(s, t)
  \/ \E s \in Contexts, t \in Contexts, a \in Artifacts : ExportArtifact(s, t, a)
  \/ \E e \in ExportUniverse : Deliver(e)
  \/ \E e \in ExportUniverse : Resolve(e)
  \/ \E s \in Contexts, t \in Contexts : SuspendRoute(s, t)
  \/ \E c \in Contexts : Withdraw(c)

LegacyAdmissionAction == \E e \in ExportUniverse : Observe(e)

=============================================================================
