------------------- MODULE NetworkCanonRefinementProofs -------------------
EXTENDS NetworkExtension, TLAPS

(***************************************************************************
Behavioral equivalence proof for ASET-NETWORK-CANON-TLA-PROJECTION-V2.

NetworkCanonProjection is standalone and does not import NetworkExtension.
The instance below explicitly maps the generated projection constants and
state onto the handwritten assurance model.  History and conditional liveness
remain separate assurance surfaces and are not claimed by this proof.
***************************************************************************)

Canon == INSTANCE NetworkCanonProjection
  WITH Contexts <- Contexts,
       Artifacts <- Artifacts,
       memberStatus <- memberStatus,
       routes <- routes,
       activeRoutes <- activeRoutes,
       exports <- exports,
       inTransit <- inTransit,
       delivered <- delivered,
       imports <- imports,
       accepted <- accepted,
       denied <- denied,
       authorityOwner <- authorityOwner,
       superiorContexts <- superiorContexts

THEOREM NetworkCanonCoreAlgebraEquivalent ==
  /\ MemberStates = Canon!CanonMemberStates
  /\ ExportUniverse = Canon!CanonExportUniverse
  /\ RouteUniverse = Canon!CanonRouteUniverse
PROOF
  BY DEF MemberStates,
         ExportUniverse,
         RouteUniverse,
         Canon!CanonMemberStates,
         Canon!CanonExportUniverse,
         Canon!CanonRouteUniverse

THEOREM NetworkCoreSafetyPredicatesEquivalentToCanonProjection ==
  /\ TypeOK <=> Canon!CanonTypeOK
  /\ NoSelfRoute <=> Canon!CanonNoSelfRoute
  /\ ActiveRouteMembersActive <=> Canon!CanonActiveRouteMembersActive
  /\ ExportBindingPreserved <=> Canon!CanonExportBindingPreserved
  /\ ImportRequiresDelivery <=> Canon!CanonImportRequiresDelivery
  /\ RecognitionRequiresImport <=> Canon!CanonRecognitionRequiresImport
  /\ TerminalRecognitionDisjoint <=> Canon!CanonTerminalRecognitionDisjoint
  /\ LocalAuthoritySovereignty <=> Canon!CanonLocalAuthoritySovereignty
  /\ NoImplicitSuperContext <=> Canon!CanonNoImplicitSuperContext
  /\ PerContextSeedProjectionWellFormed
       <=> Canon!CanonPerContextSeedProjectionWellFormed
  /\ NetworkDoesNotWeakenSeedBoundary
       <=> Canon!CanonNetworkDoesNotWeakenSeedBoundary
PROOF
  BY DEF TypeOK,
         NoSelfRoute,
         ActiveRouteMembersActive,
         ExportBindingPreserved,
         ImportRequiresDelivery,
         RecognitionRequiresImport,
         TerminalRecognitionDisjoint,
         LocalAuthoritySovereignty,
         NoImplicitSuperContext,
         ContextImports,
         ContextAccepted,
         ContextDenied,
         PerContextSeedProjectionWellFormed,
         NetworkDoesNotWeakenSeedBoundary,
         MemberStates,
         ExportUniverse,
         RouteUniverse,
         Canon!CanonTypeOK,
         Canon!CanonNoSelfRoute,
         Canon!CanonActiveRouteMembersActive,
         Canon!CanonExportBindingPreserved,
         Canon!CanonImportRequiresDelivery,
         Canon!CanonRecognitionRequiresImport,
         Canon!CanonTerminalRecognitionDisjoint,
         Canon!CanonLocalAuthoritySovereignty,
         Canon!CanonNoImplicitSuperContext,
         Canon!CanonContextImports,
         Canon!CanonContextAccepted,
         Canon!CanonContextDenied,
         Canon!CanonPerContextSeedProjectionWellFormed,
         Canon!CanonNetworkDoesNotWeakenSeedBoundary,
         Canon!CanonMemberStates,
         Canon!CanonExportUniverse,
         Canon!CanonRouteUniverse

THEOREM NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection ==
  SafetySpec <=> Canon!CanonSafetySpec
PROOF
  BY DEF SafetySpec,
         Init,
         NetworkAction,
         Resolve,
         Join,
         GrantRoute,
         ExportArtifact,
         Deliver,
         Observe,
         ResolveAccept,
         ResolveDeny,
         SuspendRoute,
         Withdraw,
         vars,
         Export,
         ExportUniverse,
         Canon!CanonSafetySpec,
         Canon!CanonInit,
         Canon!CanonNetworkAction,
         Canon!CanonResolve,
         Canon!CanonJoin,
         Canon!CanonGrantRoute,
         Canon!CanonExportArtifact,
         Canon!CanonDeliver,
         Canon!CanonObserve,
         Canon!CanonResolveAccept,
         Canon!CanonResolveDeny,
         Canon!CanonSuspendRoute,
         Canon!CanonWithdraw,
         Canon!CanonVars,
         Canon!CanonExport,
         Canon!CanonExportUniverse

=============================================================================
