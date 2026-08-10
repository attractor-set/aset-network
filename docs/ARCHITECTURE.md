# Architecture

## Three boundaries

ASET Network follows the same ownership discipline as Seed:

```text
Seed
  owns terminal recognition: UNKNOWN | ALLOW | BLOCK

Network
  owns foreign-evidence admission: imports + ADMIT_IMPORT

Federation Profile
  owns optional federation topology/lifecycle
```

### Network core

A foreign evidence object may be admitted only as an exact target-local `ImportObservation`. A successful admission is always `UNKNOWN/BLOCKED`. The core has no recognition registry, route registry, member registry, export registry or federation epoch.

```text
foreign evidence
      |
      v
ADMIT_IMPORT
      |
      v
ImportObservation (UNKNOWN / BLOCKED)
      |
      v
exact target-local Seed ResolutionBinding
```

Admission is evidence registration, not authorization.

## Seed projection

For assurance, an admitted observation maps to a fresh target-local Seed request. The target Context is the abstract local Authority and the target-scoped artifact identity is the abstract Binding. Network projects no terminal metadata and no conflicts. Consequently an admitted item remains `UNKNOWN` and never permits an effect until a later Seed-owned terminal decision outside Network state.

## Dynamic profiles

Dynamic profile definitions are immutable evidence. Exact `ProfileBinding` values project to Seed `ResolutionBinding`; applicability is derived from target-local `ALLOW`. Profiles have no universal install/enable/disable state machine and cannot weaken parent semantics.

## Federation Profile

The optional `ASET-NETWORK-FEDERATION-PROFILE-V1` owns state `{federation_id, federation_epoch, members, routes, exports}` and transitions `{FEDERATION_GENESIS, MEMBER_JOIN, ROUTE_GRANT, EXPORT_ARTIFACT, SUSPEND_ROUTE, MEMBER_WITHDRAW}`.

`imports` stays in Network. Terminal recognition stays in the pinned target-local Seed. The profile has its own executable oracle and native conformance cases; it does not depend on a historical Network release model.

Federation safety is checked in `FederationProfile.tla`. Conditional composition liveness is checked separately in `FederationCompositionLiveness.tla`; target-local resolution remains an external Seed-owned progress assumption.

## Evidence history

`history` remains a separate normative append-only trace rather than transition-enabling semantic state. It never confers Authority.
