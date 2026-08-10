# ASET Network Extension

Status: **0.1.0-alpha.3 / minimal admission core normative cutover**

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

`ASET-NETWORK-FEDERATION-PROFILE-V1` now owns the former alpha.2 federation lifecycle:

```text
FEDERATION_GENESIS
MEMBER_JOIN
ROUTE_GRANT
EXPORT_ARTIFACT
SUSPEND_ROUTE
MEMBER_WITHDRAW
```

Legacy `RECORD_RECOGNITION` is **not** transferred to the profile; terminal recognition is Seed-owned. The old 18 alpha.2 traces are retained under `legacy-alpha2-cases/` as regression evidence, and the federation-owned subset is exposed through an optional 10-case Federation Profile conformance surface.

## Dynamic profiles

`ASET-NETWORK-DYNAMIC-PROFILES-V1` adds no Network state and no Network transitions. `ProfileDefinition` and `ProfileBinding` are immutable content-addressed evidence. Applicability is derived only from target-local Seed `ALLOW` on the exact projected binding. Availability, verification or remote recognition never activates a profile.

## Formal assurance state

The alpha.3 machine canon and generated `NetworkCanonProjection.tla` are new artifacts. Therefore the alpha.2 `MECHANICALLY_PROVED` evidence is deliberately **not reused**.

This cutover ships fresh proof sources for:

1. alpha.3 canon -> `NetworkExtension.tla` behavioral equivalence;
2. minimal Network -> pinned `SeedResolution.tla` refinement;
3. legacy alpha.2 Network -> alpha.3 minimal admission refinement.

The three alpha.3 proof modules have now been rerun with the pinned TLAPM and are materialized as `MECHANICALLY_PROVED`: canon equivalence `3/3`, minimal Network -> Seed `35/35`, and legacy alpha.2 -> minimal admission `23/23`. TLC and conformance remain separate assurance surfaces and are not substitutes for TLAPS.

## Validation

Non-TLAPS validation:

```bash
python -m tools.generate_canon_tla_projection --check
python -m tools.validate_extension
python -m tools.verify_minimal_core_reduction
python -m tools.run_conformance
python -m pytest -q
python -m tools.bootstrap_tla
python -m tools.run_tlc safety
```

Local proof gates with the pinned Seed checkout:

```bash
python -m tools.run_canon_refinement_tlaps \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm

python -m tools.run_seed_refinement_tlaps \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm \
  --seed-root ~/ASET

python -m tools.run_legacy_admission_refinement_tlaps \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm
```

Apache-2.0 licensed. No implementation has semantic precedence over the machine-readable canon.
