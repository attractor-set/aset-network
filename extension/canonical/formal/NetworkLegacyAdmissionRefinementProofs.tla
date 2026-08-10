------------- MODULE NetworkLegacyAdmissionRefinementProofs -------------
EXTENDS NetworkLegacyAdmissionRefinement, TLAPS

THEOREM LegacyObservationUniverseEqualsCore ==
  ExportUniverse = Core!ObservationUniverse
PROOF
  BY DEF ExportUniverse, Core!ObservationUniverse

THEOREM LegacyInitRefinesMinimalInit ==
  Init => Core!Init
PROOF
  BY DEF Init, Core!Init

THEOREM LegacyNonAdmissionStutters ==
  LegacyNonAdmissionAction => UNCHANGED imports
PROOF
  BY DEF LegacyNonAdmissionAction, Join, GrantRoute, ExportArtifact, Deliver,
         Resolve, ResolveAccept, ResolveDeny, SuspendRoute, Withdraw

THEOREM LegacyObserveRefinesAdmit ==
  \A e \in ExportUniverse : Observe(e) => Core!AdmitImport(e)
PROOF
  BY LegacyObservationUniverseEqualsCore
     DEF Observe, Core!AdmitImport

THEOREM LegacyNetworkActionPartition ==
  NetworkAction => \/ LegacyNonAdmissionAction \/ LegacyAdmissionAction
PROOF
  BY DEF NetworkAction, LegacyNonAdmissionAction, LegacyAdmissionAction

THEOREM CoreAdmitImportIsCoreAction ==
  \A o \in Core!ObservationUniverse :
    Core!AdmitImport(o) => Core!NetworkAction
PROOF
  BY DEF Core!NetworkAction

THEOREM LegacyObserveRefinesCoreAction ==
  \A e \in ExportUniverse :
    Observe(e) => Core!NetworkAction
PROOF
  BY LegacyObservationUniverseEqualsCore,
     LegacyObserveRefinesAdmit,
     CoreAdmitImportIsCoreAction

THEOREM LegacyAdmissionRefinesCoreAction ==
  LegacyAdmissionAction => Core!NetworkAction
PROOF
  BY LegacyObserveRefinesCoreAction
     DEF LegacyAdmissionAction

THEOREM LegacyNetworkActionProjects ==
  NetworkAction => \/ Core!NetworkAction \/ UNCHANGED imports
PROOF
  BY LegacyNetworkActionPartition, LegacyNonAdmissionStutters,
     LegacyAdmissionRefinesCoreAction

THEOREM BoxLegacyNetworkActionProjects ==
  [NetworkAction]_vars => [Core!NetworkAction]_Core!vars
PROOF
  BY LegacyNetworkActionProjects
     DEF vars, Core!vars

THEOREM LegacyNetworkRefinesMinimalAdmission ==
  SafetySpec => Core!SafetySpec
PROOF
  BY PTL, LegacyInitRefinesMinimalInit, BoxLegacyNetworkActionProjects
     DEF SafetySpec, Core!SafetySpec

=============================================================================
