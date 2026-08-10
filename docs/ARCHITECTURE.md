# Architecture

## Three boundaries

ASET Network alpha.3 follows the same ownership discipline as Seed:

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

## Federation Profile after cutover

The optional `ASET-NETWORK-FEDERATION-PROFILE-V1` owns the former alpha.2 lifecycle state `{federation_id, federation_epoch, members, routes, exports}` and transitions `{FEDERATION_GENESIS, MEMBER_JOIN, ROUTE_GRANT, EXPORT_ARTIFACT, SUSPEND_ROUTE, MEMBER_WITHDRAW}`.

`imports` stays in Network. Legacy `recognitions` are Seed-derived and are not profile-owned.

The retained alpha.2 reference model is now `reference/legacy_network_reference.py`; its 18 conformance traces are regression evidence rather than core conformance. Ten traces that exercise only federation-owned operations form the Federation Profile conformance surface.

## Legacy reduction relation

The formal alpha.2 observation record and the alpha.3 assurance observation universe share the same opaque `{source,target,artifact}` shape. Therefore:

```text
legacy OBSERVE_IMPORT -> alpha.3 AdmitImport
all federation actions -> stutter on imports
legacy resolution      -> stutter on imports
```

`NetworkLegacyAdmissionRefinementProofs.tla` contains the temporal refinement theorem candidate `LegacyNetworkRefinesMinimalAdmission`. Its status is deliberately pending until the pinned local TLAPM gate succeeds.

## Evidence history

`history` remains a separate normative append-only trace rather than transition-enabling semantic state. It never confers Authority.
