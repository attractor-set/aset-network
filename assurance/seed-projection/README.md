# Seed projection assurance

`ASET-NETWORK-SEED-PROJECTION-ASSURANCE-V1` is a non-normative external
assurance perimeter for the ASET Network Extension.

It does **not** modify the Network canon and does **not** create a second source
of Seed semantics. It composes evidence already established on both sides of
one exact frozen subject:

```text
NetworkExtension SafetySpec
        |
        | NetworkExtensionRefinesSeedSafetySpec
        | mechanically proved Network -> Seed bridge
        v
exact SeedResolution.tla
        |
        | public ASET v60 bidirectional Seed/CanonicalPhase assurance
        v
canonical recognition boundary
```

The gate requires the Network refinement evidence and the public v60 assurance
package to name the same exact `SeedResolution.tla` SHA-256. A mismatch fails
closed.

## Why this is a separate gate

Network conformance answers whether an implementation or trace satisfies the
Network canon. Seed refinement answers whether the formal Network core refines
the pinned Seed. Public v60 establishes a stronger recognition-boundary
characterization of that same Seed.

This gate protects the **composition of those already-established facts**. It
prevents a later change from silently leaving Network refinement pointed at one
Seed while public recognition-boundary assurance protects another.

## Core projection contract

For the current minimal Network core:

- `imports` is the only semantic-state field;
- `ADMIT_IMPORT` is the only Network transition kind;
- `AdmitImport` refines a target-local Seed `RegisterRequest`;
- admitted evidence is `UNKNOWN` and effect-blocked;
- terminal `ALLOW` / `BLOCK` recognition remains Seed-owned.

The optional Federation Profile is checked separately for the declared
projection rule that all Federation transitions stutter on Network admission
state (`imports`). Because the Seed projection is derived from `imports`, this
is the checked Federation-to-Seed stutter boundary for this assurance profile.

## Claim boundary

This is evidence composition, not a new TLAPS theorem. The mechanically proved
relations remain the existing Network -> Seed proof and the public v60
Seed <-> CanonicalPhase proofs. The checker validates their exact shared subject,
formal artifact identities and the declared projection boundary.

Run against a local ASET checkout containing public v60:

```bash
python tools/check_seed_projection_assurance.py \
  --seed-root ~/ASET \
  --output dist/network-seed-projection-assurance.json
```

## Formal release-gate integration

The projection assurance is an external, mandatory precondition of the Network formal
release gate. The release gate deliberately uses two independent ASET checkouts:

- `--seed-root` points at the pinned Seed release used to reproduce the 35-obligation
  Network-to-Seed TLAPS refinement;
- `--assurance-root` points at the pinned public-v60 publication used to verify the
  2257-obligation assurance identity and evidence composition.

Keeping these roots distinct prevents the assurance publication identity from silently
replacing the Seed release identity used by the existing refinement proof. The gate writes
`dist/network-seed-projection-assurance.json`, binds its SHA-256 into the aggregate formal
release report, and fails closed if the projection-assurance checker fails.
