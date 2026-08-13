# ASET Network

ASET Network 0.1.0-alpha.4 is the current public representation of the minimal
cross-context evidence-admission layer for ASET Seed.

**Evidence may cross boundaries. Recognition does not.**

The Network core owns one state structure, `IMPORTS`, and one transition,
`ADMIT-IMPORT`. Admission never grants terminal recognition or permission to
execute an effect. Target-local Seed remains the recognition authority.

## Active structure

- `network/alpha4/` — the single active Network semantic line;
- `network/alpha4/operational/` — independently authored restricted-Forth representation;
- `network/alpha4/formal/` — relational representation and mechanical proof surface;
- `network/alpha4/causal/` — independently authored causal representation;
- `network/alpha4/profiles/` — Dynamic, Federation, Liveness, and Federation+Liveness subjects, each following the same three-way assurance invariant;
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the exact ASET Seed 0.4alpha three-way assurance subject;
- `history/REFERENCES.aset` — immutable identities of superseded public states only; history is not active semantics.

There is no current-pointer file. Alpha4 is current because it is the only
active semantic line under `network/`. The 0.1.0-alpha.4 representation claims
no compatibility with the 0.1.0-alpha.3 canon.

## Admission semantics

`ADMIT-IMPORT` has three bounded three-way-congruent outcomes:

- fresh identifier → `IMPORT_ADMITTED`, state changes;
- exact replay → `IDEMPOTENT_REPLAY`, state stutters;
- conflicting observation under an existing identifier → `IDENTIFIER_CONFLICT`, state stutters.

Every outcome remains fail-closed at the Seed boundary. Network does not own
`ALLOW` / `BLOCK` recognition and never permits the represented external effect
by itself.

## Three-way assurance

The Network core and every active profile subject bind independently authored
operational, relational, and causal representations with semantic precedence
`NONE`. Bounded triangulation checks operational↔relational,
operational↔causal, and relational↔causal observations. TLA/TLAPS/TLC remain
the proof/model-checking machinery for relational safety and temporal claims;
causal congruence is not described as an independent temporal proof.

Dynamic adds no Network state or transitions. Federation owns only its
profile-local lifecycle. Liveness adds no state or transition ownership and
keeps temporal claims in the relational proof surface. Federation+Liveness is
an explicit composition subject and transfers neither Authority nor
state/transition ownership.

Verify the active repository surface:

```text
python -m tools.alpha4_network_gate
python -m pytest -q
```

Mechanical Alpha4 TLAPS/TLC are executed by the repository verification
workflow with pinned tooling. The active Seed binding is checked against the
exact `seed-0.4alpha-3way` release target.

Historical identities remain in `history/REFERENCES.aset`; historical
executable theory, generated oracles, and predecessor-specific assurance tools
are intentionally not part of the active repository surface.

SHA-256 identifies exact bytes; semantic integrity is established by declared
relations and proof obligations. Generated evidence does not acquire semantic
precedence.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
