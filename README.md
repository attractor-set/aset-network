# ASET Network Extension

Status: **0.1.0-alpha.2 / federation recognition core**

ASET Network Extension defines a minimal, implementation-neutral federation layer over ASET Seed. It specifies how independent Contexts exchange content-addressed artifacts without transferring sovereignty or creating a superior Context.

## Core rule

A remote export is evidence, not authority.

Cross-context recognition follows this sequence:

```text
source export -> target import observation -> target-local Seed resolution -> local recognition receipt
```

Federation membership, ancestry, routing and source-side acceptance never authorize an effect in the target Context. Until the target-local Seed cycle returns `ACCEPT`, enforcement remains `BLOCKED`.

## Upstream binding

- Seed release: `seed-0.3.0-alpha.3`
- Seed commit: `633c130187b2a2bb42f24cfd66662d475de385d2`
- Seed canon: `ASET-SEED-RESOLUTION-CANON-0.3-ALPHA1`
- Seed canon version: `0.3.0-alpha.1`
- Seed canon package digest: `sha256:c5d48a418466ea7a60fccb7161adbd5ad568174bbc9a28fc03fd7e6e77955d31`
- Seed Compatibility Standard: `ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3`
- Compatibility profile: `ASET-SEED-COMPATIBILITY-STANDARD-V1`
- Seed conformance kit: `sha256:5ecf9b93377a062b8772b4b4b44b4d76a0997d8ba98e8711e717456abbe583db`

The pinned descriptor is stored at `upstream/ASET_SEED_BINDING.json`. This extension may strengthen Seed obligations but may not weaken them.

## Normative package

- `extension/canonical/source/network-extension-model.json`
- `extension/canonical/protocol/`
- `extension/canonical/conformance/`
- `extension/canonical/CANON_PACKAGE.json`

The Python code under `reference/` is non-normative and exists only as an executable conformance oracle.

## Formal assurance

The machine-readable canon remains normative. `NetworkExtension.tla` is an assurance projection checked with real TLC, not a replacement specification. `NetworkExtensionSeedProjection.tla` exposes the per-Context fail-closed projection toward the pinned Seed resolution algebra. `NetworkExtensionSeedRefinement.tla` and `NetworkExtensionSeedRefinementProofs.tla` define the exact bridge to the pinned upstream `SeedResolution.tla`; the upstream module is loaded externally and digest-verified rather than vendored. That refinement is mechanically proved for the pinned bridge and Seed source: `extension/canonical/assurance/seed-refinement-proof.json` records the exact artifacts, TLAPM identity, final theorems and the observed 261/261 proof-obligation result. The obligation count is evidence for this exact proof artifact, not a semantic contract.

The machine-readable canon explicitly separates the semantic network state from the canonical evidence history. Both remain normative: semantic state determines the network-state projection, while history is an append-only evidence trace. History does not itself confer Authority or alter transition eligibility unless a normative rule explicitly refers to a prior transition.

`ASET-NETWORK-LIVENESS-V1` is an optional normative capability claim, not a requirement for core `ASET-NETWORK-EXTENSION-CONFORMANCE-V1`. When claimed, it adds conditional progress guarantees under explicit fairness/environment assumptions. It requires eventual local resolution (`ACCEPT` **or** `DENY`), never eventual acceptance or global agreement.

TLC generic deadlock checking is disabled for the finite assurance configurations because intentional quiescent/model-exhausted states have no enabled domain action. Safety retains `NoUnexpectedSafetyDeadlock`, liveness checks `NoPendingProgressDeadlock` plus the temporal progress properties, and the bounded history projection checks `NoUnexpectedHistoryDeadlock`; disabling the generic check therefore does not turn stuck work into accepted behavior.

The main safety/liveness TLC state deliberately excludes the append-only execution history. Full history sequences distinguish every ordering of otherwise equivalent actions and caused factorial state-space growth without strengthening the network safety or liveness predicates. `NetworkHistory.tla` now checks `NET-INV-010` independently in a small bounded trace model (`HistoryPrefixPreserved` and `AcceptedTransitionAppendsExactlyOne`).

## Deliberately outside this alpha

Transport, peer discovery, consensus, storage, durability, key custody, cryptographic providers, homomorphic encryption, partition reconciliation and unconditional availability guarantees are implementation or later-profile responsibilities.

## Validation

```bash
python -m pip install -r requirements-ci.txt
python tools/bootstrap_tla.py
python tools/validate_extension.py
python tools/model_check_network.py
python tools/run_seed_refinement_tlaps.py \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm \
  --seed-root ~/ASET
python tools/run_formal_release_gate.py \
  --tlapm ~/ASET/.tooling/tlapm/bin/tlapm \
  --seed-root ~/ASET
python -m pytest -q
ruff check .
```

## Repository relation

- Upstream Seed: `https://github.com/attractor-set/ASET`
- This extension: `https://github.com/attractor-set/aset-network-extension`

Apache-2.0 licensed. No implementation has semantic precedence over the machine-readable canon.
