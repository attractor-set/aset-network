# ASET Network

ASET Network 0.1.0-alpha.4 is the current public representation of the minimal cross-context evidence-admission layer for ASET Seed.

**Evidence may cross boundaries. Recognition does not.**

The Network core owns one state structure, `IMPORTS`, and one transition, `ADMIT-IMPORT`. Admission never grants terminal recognition or permission to execute an effect. Target-local Seed remains the recognition authority.

## Active structure

- `network/alpha4/` — the single active Network semantic line: subject, independently authored restricted-Forth operational, TLA relational, and causal representations, pairwise congruence assurance, and optional Dynamic/Federation/Liveness profiles;
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the ASET Seed 0.4alpha three-way assurance release subject;
- `theory/network-seed-reflection/formal/` — independent historical Network→Seed reflection theory for auditing expressions of the exact Alpha3 subject;
- `history/REFERENCES.aset` — immutable identities of superseded public states; history is not active semantics.

There is no current-pointer file. Alpha4 is current because it is the only active semantic line under `network/`.

The upstream release locator is `seed-0.4alpha-3way`. It is retrieval metadata only: exact upstream identity is established by the bound source SHA-256 values, and semantic precedence remains `NONE`. The bound Seed assurance surface includes independently authored operational, relational, and causal representations; Network does not inherit Seed recognition authority.

The 0.1.0-alpha.4 representation claims no compatibility with the 0.1.0-alpha.3 canon.

## Admission semantics

`ADMIT-IMPORT` has three operational/relational/causal outcomes checked by bounded three-way congruence:

- fresh identifier → `IMPORT_ADMITTED`, state changes;
- exact replay → `IDEMPOTENT_REPLAY`, state stutters;
- conflicting observation under an existing identifier → `IDENTIFIER_CONFLICT`, state stutters.

Every outcome remains fail-closed at the Seed boundary. Network does not own `ALLOW` / `BLOCK` recognition and never permits the represented external effect by itself.

## Optional profiles

Every active profile and active profile composition follows the same three-way assurance architecture as the Network core: independently authored operational, relational, and causal representations with semantic precedence `NONE`. Dynamic adds no Network state or transitions and its causal line expresses that preserved boundary. Federation owns only its profile-local lifecycle and has its own causal lifecycle representation. Liveness has a causal enabling representation for its conditional claims while temporal properties remain checked by TLA/TLAPS/TLC. Federation+Liveness has its own three-way composition assurance and transfers neither Authority nor state/transition ownership.

Operational expression belongs to a semantic object, not specifically to a state machine or transition graph. State ownership and transition ownership are orthogonal to the existence of an operational expression.

## Three-way assurance

The active Network core, Dynamic, Federation, Liveness, and Federation+Liveness composition each bind three independently authored representation lines: operational, relational, and causal. No representation is generated from another and semantic precedence is `NONE`. Bounded triangulation checks operational↔relational, operational↔causal, and relational↔causal observations. TLA/TLAPS/TLC remain the proof/model-checking machinery for relational safety and temporal claims; causal congruence is not described as an independent temporal proof.

    python -m tools.alpha4_network_assurance

## Independent historical expression assurance

The historical reflection theory is source material, not a checked-in oracle dataset. It contains only TLA modules. The black-box oracle and its four bounded witnesses are generated deterministically from that theory plus exact identities in `history/REFERENCES.aset`.

The generated assurance covers the complete historical admission surface:

- fresh admission → proved Seed `RegisterRequest` refinement;
- exact replay → proved Seed stutter;
- identifier conflict → proved Seed stutter;
- all observed outcomes remain `UNKNOWN` / `BLOCKED` with `effect_permitted=false`.

Generate the oracle artifact:

    python -m tools.network_seed_reflection_oracle \
      --output dist/network-seed-reflection-oracle.json

Re-prove the reflection against the exact historical Seed subject:

    python -m tools.run_network_seed_reflection_tlaps \
      --tlapm <pinned-tlapm> \
      --seed-root <exact-seed-0.3.0-alpha.3-checkout>

Then audit any compatible external expression through the black-box protocol:

    python -m tools.check_network_expression_assurance \
      --proof-evidence dist/network-seed-reflection-proof.json \
      --adapter-command '<external-adapter-command>'

The checker imports neither implementation internals nor a Python reference oracle. An expression must explicitly bind itself to the exact historical subject; similar behavior is not treated as identity.

## Verification

    python -m tools.validate_repository_minimal
    python -m tools.alpha4_network_gate
    python -m pytest -q

Mechanical Alpha4 TLAPS/TLC and historical reflection TLAPS are executed by the repository verification workflow with pinned tooling and exact upstream subjects. The active Seed binding is verified against the exact `seed-0.4alpha-3way` release target.

SHA-256 identifies exact bytes; semantic integrity is established by declared relations and proof obligations. Generated evidence does not acquire semantic precedence.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
