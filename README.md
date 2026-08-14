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

Network extends the exact Seed subject representation-by-representation rather
than restating Seed semantics: operational `OBSERVE-UNKNOWN` binds only to accepted `ADMIT-FRESH` /
`ADMIT-REPLAY` branches, relational `ObserveUnknown` binds only to
`AdmitFresh` / `AdmitReplay`, and the causal `OBSERVE-UNKNOWN` boundary binds
only to the corresponding accepted causal branches. `REJECT-CONFLICT` does not
claim a Seed transition. The three bindings are checked independently and Seed
redefinition is not admitted.

Dynamic adds no Network state or transitions. Federation owns only its
profile-local lifecycle. Liveness adds no state or transition ownership and
keeps temporal claims in the relational proof surface. Federation+Liveness is
an explicit composition subject and transfers neither Authority nor
state/transition ownership.

## Release materialization

English and Python are downstream release companions, not additional assurance
representations. The Network English companion extends the exact Seed English
companion. The Network Python companion loads and verifies the exact Seed Python
companion bytes and delegates accepted imports to Seed `OBSERVE-UNKNOWN`; it does
not contain a second Seed recognition engine. Both companions have semantic
precedence `NONE`.

The release builder materializes `formal/AssembledNetwork.tla` after source
assurance. A separate post-build TLAPS verifier proves that the assembled Network
accepted-import projection is compatible with the exact released Seed
`ObserveUnknown` relation for the same evidence digest, while rejected imports
claim no Seed transition. It runs against the exact released
`ComponentRelations.tla` in an isolated temporary directory and verifies that
neither release tree changes during proof execution. The generated Python extension is then checked through
an independent bounded air-gap over the same 446 Network assurance cases before
release admission.

```text
source Forth / TLA / Petri
          |
          v
   three-way assurance
          |
          v
    source TLAPS/TLC
          |
          v
         build
          |
          v
 AssembledNetwork.tla
          |
          v
 post-build exact-Seed TLAPS
          |
       +--+--+
       |     |
    English Python
       |     |
       |   air-gap
       +--+--+
          |
          v
   release admission
```

Verify the active source surface with `python -m tools.alpha4_network_gate`.
The complete release gate is `tools.alpha4_network_release_gate.py`; CI supplies
the exact immutable Seed source, release tree, companion tree, and pinned TLAPM.
The Seed release bytes remain those published under `seed-0.4alpha-3way`.

Historical identities remain in `history/REFERENCES.aset`; historical
executable theory, generated oracles, and predecessor-specific assurance tools
are intentionally not part of the active repository surface.

SHA-256 identifies exact bytes; semantic integrity is established by declared
relations and proof obligations. Generated evidence does not acquire semantic
precedence.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
