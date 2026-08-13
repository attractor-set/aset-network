# Architecture

## Three boundaries

ASET Network follows the same ownership discipline as Seed:

```text
Seed
  owns terminal recognition: UNKNOWN | ALLOW | BLOCK

Network
  owns foreign-evidence admission: imports + ADMIT_IMPORT

Profiles
  Dynamic Profile contract
  Federation Profile -> owns optional federation topology/lifecycle
  Liveness Profile -> owns optional conditional progress claims
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

## Operational-expression boundary

Restricted Forth is an operational representation of a semantic object, not a privilege of stateful transition systems. State ownership and transition ownership are independent of whether an operational expression exists. Transition subjects may use transition evaluators; relation subjects may use predicates; property/trace subjects may use finite witness recognizers; assurance compositions may use composition predicates. None of those operational forms creates state, transitions or Authority that the subject does not already own.

## Federation Profile

The optional `ASET-NETWORK-FEDERATION-PROFILE-V1` owns state `{federation_id, federation_epoch, members, routes, exports}` and transitions `{FEDERATION_GENESIS, MEMBER_JOIN, ROUTE_GRANT, EXPORT_ARTIFACT, SUSPEND_ROUTE, MEMBER_WITHDRAW}`.

`imports` stays in Network. Terminal recognition stays in the pinned target-local Seed. The frozen Alpha3 predecessor profile has its own non-normative executable oracle and native conformance cases; Alpha4 instead uses paired operational/relational expressions and does not derive semantic authority from that historical oracle.

Federation safety is checked by the profile-local assurance module `profiles/federation/assurance/FederationProfile.tla`. `ASET-NETWORK-LIVENESS-V1` is a separate profile with no state or transition ownership. Their compatibility is checked by the separate assurance relation under `assurance/profile-compositions/federation-liveness/`; target-local resolution remains an external Seed-owned progress assumption.

## Evidence history

`history` remains a separate normative append-only trace rather than transition-enabling semantic state. It never confers Authority.

## Profile directory boundary

Every optional profile is a separate canonical entity under `extension/canonical/profiles/<profile>/`. Core protocol, conformance and formal directories contain core artifacts only. Cross-profile assurance belongs under `extension/canonical/assurance/profile-compositions/` and MUST NOT be used to imply profile inheritance.
