# ASET Network Extension

Status: **0.1.0-alpha.3 / minimal admission core**

ASET Network Extension is the minimal implementation-neutral boundary by which foreign evidence becomes a target-local candidate for ASET Seed resolution.

## Core rule

**Evidence may cross boundaries. Recognition does not.**

The universal Network core now owns exactly one semantic state structure and one mutation:

```text
foreign evidence -> ADMIT_IMPORT -> target-local UNKNOWN/BLOCKED import -> Seed
```

`imports` is the only Network semantic-state field. `ADMIT_IMPORT` is the only Network transition kind. Admission never authorizes an effect and never creates terminal recognition. `ALLOW` / `BLOCK` remain exclusively target-local Seed semantics.

Federation membership, routing, source export lifecycle and conditional liveness are optional profile concerns, not Network-core semantics. Any terminal-resolution liveness claim is explicitly target-local Seed-owned.

## Upstream binding

- Seed release: `seed-0.3.0-alpha.3`
- Seed commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Seed canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Seed canon package digest: `sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

The exact descriptor is `upstream/ASET_SEED_BINDING.json`. Network may strengthen Seed constraints but may not weaken or supersede them.

## Normative surfaces

- `extension/canonical/source/network-extension-model.json` — minimal admission canon.
- `extension/canonical/protocol/` — core wire objects plus optional profile surfaces.
- `extension/canonical/conformance/cases/` — four alpha.3 core cases.
- `extension/canonical/CANON_PACKAGE.json` — complete canon package.

The Python implementations under `reference/` are non-normative conformance oracles.

## Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` is an optional dynamic profile with its own lifecycle state and transitions:

```text
FEDERATION_GENESIS
MEMBER_JOIN
ROUTE_GRANT
EXPORT_ARTIFACT
SUSPEND_ROUTE
MEMBER_WITHDRAW
```

The profile has a native non-normative oracle at `reference/federation_profile_reference.py` and an independent 10-case conformance surface under `extension/canonical/conformance/federation-profile-cases/`. Federation transitions stutter with respect to Network admission state. Terminal recognition is not a Federation operation and remains exclusively target-local Seed-owned.

## Dynamic profiles

`ASET-NETWORK-DYNAMIC-PROFILES-V1` adds no Network state and no Network transitions. `ProfileDefinition` and `ProfileBinding` are immutable content-addressed evidence. Applicability is derived only from target-local Seed `ALLOW` on the exact projected binding. Availability, verification or remote recognition never activates a profile.

## Formal assurance state

The current proof chain has two mechanically proved TLAPS relations:

1. machine canon -> `NetworkExtension.tla` behavioral equivalence;
2. minimal Network -> pinned `SeedResolution.tla` refinement.

The materialized results are canon equivalence `3/3` and minimal Network -> Seed `35/35`. The optional Federation Profile has separate bounded TLC safety and composition-liveness models: `FederationProfile.tla` and `FederationCompositionLiveness.tla`. The liveness model treats `Resolve(e)` only as an assurance witness of target-local Seed progress; it creates no Network- or Federation-owned recognition state.

## Validation

Non-TLAPS validation:

```bash
python -m tools.generate_canon_tla_projection --check
python -m tools.validate_extension
python -m tools.run_conformance
python -m pytest -q
python -m tools.bootstrap_tla
python -m tools.run_tlc all
```

Local proof gates with the pinned Seed checkout:

```bash
python -m tools.run_canon_refinement_tlaps \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm

python -m tools.run_seed_refinement_tlaps \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm \
  --seed-root ~/ASET
```

Apache-2.0 licensed. No implementation has semantic precedence over the machine-readable canon.
