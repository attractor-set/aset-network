# Formal verification architecture

ASET Network Alpha4 is the current public representation. No single operational,
relational, proof, binding or current-selection artifact has semantic precedence.
The Network subject is expressed independently and related mechanically.

## Current Alpha4 core chain

```text
network/alpha4/NETWORK.aset
        |
        +-------------------------------+
        |                               |
        v                               v
restricted Forth                 NetworkRelations.tla
operational expression           relational expression
        |                               |
        +-------------+-----------------+
                      |
                      v
OperationalRelationalPairingProofs.tla
                      |
                      v
SeedBoundaryProofs.tla
                      |
                      v
content-addressed ASET Seed 0.4alpha boundary
```

The current-selection pointer is `network/CURRENT.aset`. It is project metadata
with `SEMANTIC-PRECEDENCE NONE`; promotion does not alter the Alpha4 subject or
its paired expressions.

## Current Alpha4 profiles

Dynamic, Federation and Liveness are separate optional profile subjects under
`network/alpha4/profiles/`. Federation owns its profile-local lifecycle state and
transitions. Dynamic and Liveness own no Network state or transitions but still
have operational expressions because operational representation belongs to the
semantic object rather than to a state machine.

The profile proof runner checks operational/relational pairings and ownership
boundaries. TLC independently checks Federation safety and the temporal
Federation+Liveness progress composition.

```text
python -m tools.run_alpha4_network_tlaps --tlapm <tlapm>
python -m tools.run_alpha4_network_profile_tlaps --tlapm <tlapm>
python -m tools.run_alpha4_network_profile_tlc
```

## Frozen Alpha3 predecessor assurance

`extension/canonical/**` is the byte-frozen Alpha3 predecessor representation.
Its canon-to-TLA relation, Seed refinement, conformance cases and historical
profile assurance remain reproducible regression evidence. They are not the
current Network semantic surface and do not acquire precedence over Alpha4.

The Alpha3 tools remain in CI specifically to detect predecessor drift:

```text
python -m tools.validate_extension
python -m tools.run_conformance
python -m tools.build_formal_relation --check
python -m tools.build_canon_package --check
```
