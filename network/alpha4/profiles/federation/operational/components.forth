: FEDERATION-GENESIS ( profile federation-id epoch network -- profile network result )  EMPTY-FEDERATION? CREATE-FEDERATION KEEP-NETWORK FEDERATION-CREATED ;
: MEMBER-JOIN        ( profile context network -- profile network result )             FEDERATION? MEMBER-ABSENT? ADD-MEMBER KEEP-NETWORK MEMBER-JOINED ;
: ROUTE-GRANT        ( profile source target network -- profile network result )       ACTIVE-MEMBERS? DISTINCT-ENDPOINTS? ROUTE-ABSENT? ADD-ACTIVE-ROUTE KEEP-NETWORK ROUTE-GRANTED ;
: EXPORT-ARTIFACT    ( profile source target artifact network -- profile network result ) ACTIVE-ROUTE? EXPORT-ABSENT? ADD-EXPORT KEEP-NETWORK ARTIFACT-EXPORTED ;
: SUSPEND-ROUTE      ( profile source target network -- profile network result )       ACTIVE-ROUTE? SUSPEND-ACTIVE-ROUTE KEEP-NETWORK ROUTE-SUSPENDED ;
: MEMBER-WITHDRAW    ( profile context network -- profile network result )             ACTIVE-MEMBER? NO-ACTIVE-ROUTE? WITHDRAW-MEMBER KEEP-NETWORK MEMBER-WITHDRAWN ;
