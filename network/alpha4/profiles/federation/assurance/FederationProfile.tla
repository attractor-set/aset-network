---------------------- MODULE FederationProfile ----------------------
EXTENDS FederationRelations

CONSTANTS InitialNetworkImports
VARIABLES federation, networkImports
vars == <<federation, networkImports>>

Init ==
  /\ EmptyFederationState(federation)
  /\ networkImports = InitialNetworkImports

Next == FederationStep(federation, federation', networkImports, networkImports')
Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ federation \in FederationStateType
  /\ networkImports = InitialNetworkImports

NoSelfRoute ==
  \A route \in RouteUniverse :
    federation.routes[route] # "ABSENT" => route[1] # route[2]

ActiveRouteMembersActive ==
  \A route \in RouteUniverse :
    federation.routes[route] = "ACTIVE" =>
      /\ federation.members[route[1]] = "ACTIVE"
      /\ federation.members[route[2]] = "ACTIVE"

ExportBindingPreserved ==
  \A export \in federation.exports :
    federation.routes[<<export.source, export.target>>] # "ABSENT"

=============================================================================
