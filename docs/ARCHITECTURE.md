# Architecture

## Sovereignty boundary

Each member is an independent Context with its own Constitution, Authority, canonical state and policy epoch. The federation stores composition and routing facts; it does not become an Authority for member-local decisions.

## Recognition pipeline

1. The source Context emits a content-addressed Export under an exact active RouteGrant.
2. The target Context records an ImportObservation as `UNKNOWN/BLOCKED`.
3. The target opens or binds an ASET Seed resolution cycle using its own ContextBinding and ResolutionAuthority.
4. A terminal Seed result is recorded as a local RecognitionReceipt.
5. Only target-local `ACCEPT/ALLOW` can authorize a later effect. Effect execution is outside this extension.

## Metafederation

A metafederation is a graph or composition of federations. It does not imply a root Context, a global Constitution or inherited Resolution Authority. Cross-federation recognition repeats the same local pipeline at every sovereign boundary.
