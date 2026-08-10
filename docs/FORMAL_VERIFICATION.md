# Formal verification architecture

The machine-readable canon is normative. TLA+ artifacts provide assurance and never override it.

## Current core chain

```text
network-extension-model.json
        |
        | deterministic generation
        v
NetworkCanonProjection.tla
        |
        | TLAPS 3/3
        v
NetworkExtension.tla
        |
        +-- TLC minimal safety
        +-- NetworkHistory.tla -> append-only trace
        |
        | TLAPS 35/35
        v
pinned SeedResolution.tla
```

The projection profile is `ASET-NETWORK-CANON-TLA-PROJECTION-V3`. The handwritten Network model has exactly one variable, `imports`, and one state-changing action, `AdmitImport`.

## Profile assurance

Federation lifecycle and liveness are separate optional profiles rather than Network-core semantics. Their current bounded assurance surfaces are:

- `extension/canonical/profiles/federation/assurance/FederationProfile.tla` / `.cfg` — Federation Profile lifecycle safety;
- `extension/canonical/profiles/liveness/` — independent Liveness Profile contract;
- `extension/canonical/assurance/profile-compositions/federation-liveness/FederationCompositionLiveness.tla` / `.cfg` — bounded assurance for composing Federation and Liveness as peer profiles.

`Resolve(e)` in the composition assurance is not a Network, Federation or Liveness transition. It is an assurance witness for the explicitly declared target-local Seed progress assumption. The composition does not establish a parent relation between profiles.

## Reproducibility gates

```text
python -m tools.generate_canon_tla_projection --check
python -m tools.validate_extension
python -m tools.run_conformance
python -m tools.run_tlc all
```

The two TLAPS proof runners shown in the repository README reproduce the materialized canon and Seed refinement evidence. A proof runner must fail if the current proof source hash, pinned toolchain, theorem set, or recorded obligation count does not match the evidence.
