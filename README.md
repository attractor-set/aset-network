# ASET Network

Status: **Alpha4 current public representation / Alpha3 frozen predecessor evidence**

ASET Network is the minimal implementation-neutral boundary by which foreign evidence becomes a target-local candidate for ASET Seed resolution.

## Alpha4 paired admission

The current Alpha4 surface lives under `network/alpha4/`. `network/CURRENT.aset` selects it as the current project representation without granting semantic precedence. It reduces the Network-owned semantic subject to exact import observations plus the single `ADMIT-IMPORT` operation, expressed twice and checked for congruence:

- `network/alpha4/operational/components.forth` — restricted operational expression;
- `network/alpha4/formal/NetworkRelations.tla` — independent relational expression;
- `network/alpha4/formal/OperationalRelationalPairingProofs.tla` — pairing proof;
- `network/alpha4/formal/SeedBoundaryProofs.tla` — proof that accepted admission projects only to target-local Seed `UNKNOWN` and never permits an effect;
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the active ASET Seed 0.4alpha semantic sources.

The existing `extension/canonical/**` Alpha3 package remains byte-frozen predecessor evidence and regression material. The current Alpha4 representation does not inherit Alpha3 compatibility claims and does not make the historical Python core oracle authoritative.

Verify the current representation locally:

```bash
python -m tools.alpha4_network_gate
python -m pytest -q tests/test_alpha4_network.py
```

## Alpha4 optional profiles

The current Alpha4 representation carries its optional profile semantics under `network/alpha4/profiles/` without changing `network/alpha4/NETWORK.aset`:

- `dynamic/DYNAMIC.aset` — exact target-local Seed `ALLOW` activation contract; adds no Network state or transitions;
- `federation/FEDERATION.aset` — profile-local federation lifecycle with five owned state fields and six transitions, all specified to stutter on Network `IMPORTS`;
- `liveness/LIVENESS.aset` — conditional progress contract; adds no Network state or transitions and never requires eventual `ALLOW`;
- `composition/federation-liveness/FEDERATION_LIVENESS.aset` — assurance-only capability composition with no profile parent relation, state/transition ownership transfer or Authority transfer.

Every Alpha4 profile semantic object now has paired operational and relational expressions. Federation pairs its lifecycle transition graph in Forth/TLA; Dynamic pairs its exact-binding activation relation; Liveness pairs its conditional claim/result predicates without adding a transition machine; and Federation+Liveness pairs its capability/boundary composition predicate. TLAPS proves the pairings and boundaries, while TLC remains responsible for Federation safety and the temporal Federation+Liveness progress model. The liveness progress harness treats target observation as an assurance witness for Network-owned `ADMIT-IMPORT` and terminal resolution as an assurance witness for Seed-owned resolution.

Verify the profile layer locally:

```bash
python -m tools.alpha4_network_profiles_gate
python -m tools.alpha4_network_profile_paired_expression
python -m pytest -q tests/test_alpha4_network_profiles.py
python -m tools.run_alpha4_network_profile_tlaps --tlapm ~/aset-seed/.tooling/tlapm/bin/tlapm
python -m tools.run_alpha4_network_profile_tlc
```

## Operational expressions are semantic-object based

An operational expression belongs to a **semantic object**, not specifically to a state machine or transition graph. State ownership and transition ownership are therefore orthogonal to the existence of a restricted-Forth expression.

The form of the operational expression follows the semantic object:

- transition subjects use transition evaluators;
- relational subjects use operational predicates;
- property subjects use claim predicates;
- trace subjects use finite-witness recognizers;
- composition subjects use composition predicates.

Dynamic and Liveness demonstrate the boundary directly: both own no Network state and define no Network transitions, yet both have restricted-Forth operational expressions paired with independent TLA relational expressions. Federation remains the stateful profile; its Forth expression evaluates its profile-owned lifecycle transition graph.

```text
semantic object
    ├── operational expression   (restricted Forth)
    └── relational expression    (TLA)
             ↕
          pairing

state ownership        independent
transition ownership   independent
```

Accordingly, `operational expression` does **not** imply `state ownership`, `transition ownership`, or state-machine semantics. The machine-readable profile contract enforces this with `OPERATIONAL-EXPRESSION-REQUIRES-STATE NEVER` and `OPERATIONAL-EXPRESSION-REQUIRES-TRANSITION NEVER`.

## Core rule

**Evidence may cross boundaries. Recognition does not.**

The universal Network core now owns exactly one semantic state structure and one mutation:

```text
foreign evidence -> ADMIT_IMPORT -> target-local UNKNOWN/BLOCKED import -> Seed
```

`imports` is the only Network semantic-state field. `ADMIT_IMPORT` is the only Network transition kind. Admission never authorizes an effect and never creates terminal recognition. `ALLOW` / `BLOCK` remain exclusively target-local Seed semantics.

Federation membership/routing and conditional liveness are separate optional profiles, not Network-core semantics. The Federation Profile owns federation lifecycle only; the Liveness Profile owns conditional progress claims only. They may be composed without either becoming the parent of the other. Any terminal-resolution progress assumption remains explicitly target-local Seed-owned.

## Direct repository topology

- Upstream specification: [ASET Seed](https://github.com/attractor-set/aset-seed) — direct normative parent.

Only direct repository relationships are listed here. Transitive relationships are discovered through their immediate parent repositories.

## Frozen Alpha3 upstream binding

- Seed release: `seed-0.3.0-alpha.3`
- Seed commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Seed canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Seed canon package digest: `sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31`
- Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`

The exact descriptor is `upstream/ASET_SEED_BINDING.json`. Network may strengthen Seed constraints but may not weaken or supersede them.

## Frozen Alpha3 surfaces

- `extension/canonical/source/network-extension-model.json` — minimal admission canon.
- `extension/canonical/protocol/` — core wire objects only.
- `extension/canonical/profiles/` — separate optional profile entities.
- `extension/canonical/conformance/cases/` — four alpha.3 core cases.
- `extension/canonical/CANON_PACKAGE.json` — complete canon package.

The Python implementations under `reference/` are non-normative conformance oracles.

## Frozen Alpha3 Federation Profile

`ASET-NETWORK-FEDERATION-PROFILE-V1` is an optional dynamic profile with its own lifecycle state and transitions:

```text
FEDERATION_GENESIS
MEMBER_JOIN
ROUTE_GRANT
EXPORT_ARTIFACT
SUSPEND_ROUTE
MEMBER_WITHDRAW
```

All Federation-owned artifacts live under `extension/canonical/profiles/federation/`. The profile has a native non-normative oracle at `reference/profiles/federation.py` and an independent 10-case conformance surface. Federation transitions stutter with respect to Network admission state. Terminal recognition and liveness are not Federation operations.

## Frozen Alpha3 Dynamic profiles

`ASET-NETWORK-DYNAMIC-PROFILES-V1` adds no Network state and no Network transitions. `ProfileDefinition` and `ProfileBinding` are immutable content-addressed evidence. Applicability is derived only from target-local Seed `ALLOW` on the exact projected binding. Availability, verification or remote recognition never activates a profile.

## Frozen Alpha3 Liveness Profile

`ASET-NETWORK-LIVENESS-V1` is an independent optional dynamic profile. It owns no Network state and no transition kinds. It declares conditional progress guarantees and the capabilities required from a separately composed profile. The currently checked composition pairs it with `ASET-NETWORK-FEDERATION-PROFILE-V1`; that pairing is assurance evidence, not a parent/child relationship.

## Formal assurance state

The current Alpha4 assurance chain is the paired-expression architecture under `network/alpha4/**`:

1. the restricted-Forth core expression is paired with the independent TLA relational core;
2. `SeedBoundaryProofs.tla` proves the target-local Seed recognition boundary;
3. Dynamic, Federation, Liveness and Federation+Liveness each carry independent operational/relational assurance appropriate to their semantic object;
4. Federation safety and Federation+Liveness temporal progress are checked with TLC.

`python -m tools.alpha4_network_gate` is the primary current-representation gate. The frozen Alpha3 canon/refinement tools remain regression gates for predecessor evidence only; they do not define the current Network representation.

## Validation

Current Alpha4 representation:

```bash
python -m tools.validate_current_network
python -m tools.alpha4_network_gate
python -m tools.validate_alpha4_network --seed-root ~/aset-seed
python -m tools.run_alpha4_network_tlaps --tlapm ~/aset-seed/.tooling/tlapm/bin/tlapm
python -m tools.run_alpha4_network_profile_tlaps --tlapm ~/aset-seed/.tooling/tlapm/bin/tlapm
python -m tools.run_alpha4_network_profile_tlc
python -m pytest -q
```

Frozen Alpha3 predecessor regression:

```bash
python -m tools.validate_extension
python -m tools.run_conformance
python -m tools.build_formal_relation --check
python -m tools.build_canon_package --check
```

Apache-2.0 licensed. No implementation, current-selection pointer or frozen predecessor artifact has semantic precedence over the Alpha4 semantic subjects and their mechanically paired expressions.
