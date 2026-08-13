# ASET Network

ASET Network 0.1.0-alpha.4 is the current public representation of the minimal cross-context evidence-admission layer for ASET Seed.

**Evidence may cross boundaries. Recognition does not.**

The Network-owned core has one semantic state structure, `IMPORTS`, and one transition, `ADMIT-IMPORT`. A successful admission creates only target-local `UNKNOWN` evidence and never permits an effect; terminal `ALLOW` / `BLOCK` recognition remains Seed-owned.

Active structure:

- `network/alpha4/` — current Network subject, restricted-Forth operational expressions, independent TLA relational expressions, pairing proofs and optional Dynamic/Federation/Liveness profiles;
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the active ASET Seed 0.4alpha semantic sources;
- `theory/network-seed-reflection/` — retained Alpha3 Network→Seed theorem corpus used only as an independent black-box oracle for expressions of that exact historical subject;
- `history/REFERENCES.aset` — immutable identities of superseded public states; history is not active semantics;
- `tools/alpha4_network_gate.py` — complete current-representation gate;
- `tools/validate_repository_minimal.py` — repository-surface minimality gate.

The 0.1.0-alpha.4 representation claims no compatibility with the 0.1.0-alpha.3 canon.

## Optional profiles

Dynamic adds no Network state or transitions and activates only from exact target-local Seed recognition. Federation owns only its profile-local lifecycle. Liveness adds conditional progress claims without requiring eventual `ALLOW`. Federation+Liveness composition transfers neither Authority nor state/transition ownership. Every profile semantic object has paired operational and relational expressions; operational expression does not imply state-machine semantics.

## Independent expression assurance

The retained Alpha3 theorem corpus is not a legacy semantic authority. It is an independent external oracle for a black-box expression that explicitly binds itself to the exact historical Alpha3 subject. The checker does not import implementation internals or a Python reference oracle. Fresh admissions must commute through the mechanically proved Network→Seed bridge as Seed `RegisterRequest` with `UNKNOWN` and `effect_permitted=false`.

Run the black-box checker against a compatible external adapter:

    python tools/check_network_expression_assurance.py \
      --adapter-command 'python -m aset_network_python_sqlite.adapter'

An Alpha2-bound implementation is rejected; historical-subject identity is exact, not inferred from similar behavior.

## Verification

    python -m tools.validate_repository_minimal
    python -m tools.alpha4_network_gate
    python -m pytest -q

For mechanical proofs, run the Alpha4 TLAPS/profile-TLC gates and `tools/run_network_seed_reflection_tlaps.py` with the pinned TLAPM and exact historical Seed checkout.

SHA-256 identifies exact bytes; semantic integrity is established by declared congruence and proof obligations. Historical references do not acquire semantic precedence.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
