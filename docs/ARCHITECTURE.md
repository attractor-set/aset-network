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

`imports` stays in Network. Terminal recognition stays in the target-local ASET Seed 0.4alpha subject selected through the content-addressed Alpha4 binding. The frozen Alpha3 predecessor profile has its own non-normative executable oracle and native conformance cases; Alpha4 instead uses paired operational/relational expressions and does not derive semantic authority from that historical oracle.

Federation safety is checked by the profile-local assurance module `profiles/federation/assurance/FederationProfile.tla`. `ASET-NETWORK-LIVENESS-V1` is a separate profile with no state or transition ownership. Their compatibility is checked by the separate assurance relation under `assurance/profile-compositions/federation-liveness/`; target-local resolution remains an external Seed-owned progress assumption.

## Frozen Alpha3 evidence history

The Alpha3 `history` trace remains frozen predecessor evidence rather than current transition-enabling semantic state. It never confers Authority over Alpha4.

## Profile directory boundary

Current optional profile subjects live under `network/alpha4/profiles/<profile>/`. Their operational and relational expressions remain profile-local, and cross-profile assurance cannot imply profile inheritance, state ownership transfer or Authority transfer.

`extension/canonical/profiles/**` and `extension/canonical/assurance/profile-compositions/**` are frozen Alpha3 predecessor surfaces retained only for regression and historical evidence.
