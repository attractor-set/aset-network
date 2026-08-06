# ASET Network Extension

Status: **0.1.0-alpha.1 / federation recognition core**

ASET Network Extension defines a minimal, implementation-neutral federation layer over ASET Seed. It specifies how independent Contexts exchange content-addressed artifacts without transferring sovereignty or creating a superior Context.

## Core rule

A remote export is evidence, not authority.

Cross-context recognition follows this sequence:

```text
source export -> target import observation -> target-local Seed resolution -> local recognition receipt
```

Federation membership, ancestry, routing and source-side acceptance never authorize an effect in the target Context. Until the target-local Seed cycle returns `ACCEPT`, enforcement remains `BLOCKED`.

## Upstream binding

- Seed canon: `ASET-SEED-RESOLUTION-CANON-0.2-ALPHA1`
- Seed version: `0.2.0-alpha.1`
- Seed conformance protocol: `ASET-SEED-RESOLUTION-CONFORMANCE-V1`
- Pinned `CANON_PACKAGE.json` file digest: `sha256:fb4638962eb3fbb19ca18f46066d28e97e037c709b1a4b99bceab68e32e523db`
- Pinned Seed internal package digest: `sha256:52862a9564a08cfb765ca1cc9d5551d439c75660f1fd11851e8d30d6ff7b1b8e`

The pinned descriptor is stored at `upstream/ASET_SEED_BINDING.json`. This extension may strengthen Seed obligations but may not weaken them.

## Normative package

- `extension/canonical/source/network-extension-model.json`
- `extension/canonical/protocol/`
- `extension/canonical/conformance/`
- `extension/canonical/CANON_PACKAGE.json`

The Python code under `reference/` is non-normative and exists only as an executable conformance oracle.

## Deliberately outside this alpha

Transport, peer discovery, consensus, storage, durability, key custody, cryptographic providers, homomorphic encryption, partition reconciliation and availability guarantees are implementation or later-profile responsibilities.

## Validation

```bash
python -m pip install -r requirements-ci.txt
python tools/validate_extension.py
python tools/model_check_network.py
python -m pytest -q
ruff check .
```

## Repository relation

- Upstream Seed: `https://github.com/attractor-set/ASET`
- This extension: `https://github.com/attractor-set/aset-network-extension`

Apache-2.0 licensed. No implementation has semantic precedence over the machine-readable canon.
