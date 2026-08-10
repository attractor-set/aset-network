# Formal verification architecture

The machine-readable canon is normative. TLA+ artifacts provide assurance and never override it.

## Alpha.3 chain

```text
network-extension-model.json
        |
        | deterministic generation
        v
NetworkCanonProjection.tla
        |
        | TLAPS proof source
        v
NetworkExtension.tla
        |
        +-- TLC minimal safety
        +-- NetworkHistory.tla -> append-only trace
        |
        | separate TLAPS proof source
        v
pinned SeedResolution.tla
```

The projection profile is `ASET-NETWORK-CANON-TLA-PROJECTION-V3`. The handwritten Network model has exactly one variable, `imports`, and one state-changing action, `AdmitImport`.

## Cutover proof status

Alpha.3 changes the normative model, generated projection and Seed mapping. The alpha.2 proof evidence therefore was not inherited. The new exact alpha.3 artifacts have now been rerun with the pinned TLAPM and the proof-evidence records are materialized as `MECHANICALLY_PROVED`.

Fresh proof sources are:

- `NetworkCanonRefinementProofs.tla` — generated canon -> handwritten minimal model;
- `NetworkExtensionSeedRefinementProofs.tla` — minimal model -> pinned Seed;
- `NetworkLegacyAdmissionRefinementProofs.tla` — alpha.2 legacy model -> minimal admission projection.

Materialized TLAPS results:

- canon -> handwritten minimal Network: `3/3` obligations proved;
- minimal Network -> pinned Seed: `35/35` obligations proved;
- legacy alpha.2 -> minimal admission: `23/23` obligations proved.

A TLC pass checks a bounded state space. It is not a substitute for any of these TLAPS claims.

## Legacy refinement

`NetworkLegacyAlpha2.tla` preserves the previous assurance model as an historical proof source. The cutover mapping instantiates alpha.3 `NetworkExtension` on the legacy `imports` variable. `Observe` refines `AdmitImport`; all other legacy actions stutter with respect to `imports`. The mechanically proved final theorem is:

```text
LegacyNetworkRefinesMinimalAdmission ==
    SafetySpec => Core!SafetySpec
```

## Reproducibility gates

```text
python tools/generate_canon_tla_projection.py --check
python tools/validate_extension.py
python tools/run_conformance.py
python tools/run_tlc.py safety
```

The three TLAPS proof runners shown in the repository README reproduce the materialized evidence. A proof runner must fail if the current proof source hash, pinned toolchain, theorem set, or recorded obligation count does not match the evidence.
