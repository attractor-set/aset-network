# Migration from the predecessor lifecycle canon

The current Network `0.1.0-alpha.3` release is pinned to ASET Seed `seed-0.3.0-alpha.3`. Seed intentionally keeps federation topology and Context lifecycle outside its minimal resolution core. Network alpha.3 likewise does **not** reintroduce federation into the universal Network core: it retains only target-local admission of foreign evidence, while federation lifecycle is an optional Seed-bound profile.

Historical concepts retained in narrowed form:

- Context remains the normative namespace boundary;
- ancestry or federation membership does not imply Authority;
- profile-produced export -> Network `ADMIT_IMPORT` -> target-local Seed resolution is a composition across separate owners;
- membership withdrawal and route lifecycle belong to `ASET-NETWORK-FEDERATION-PROFILE-V1`;
- federation and metafederation do not create superior sovereignty.

Not migrated into the universal Network core:

- federation identity, membership or routes;
- source export lifecycle;
- terminal recognition;
- partition-local transition classes or fork reconciliation;
- Context redefinition and transitive sibling consent;
- alias lifecycle;
- cryptographic, transport and storage choices.

Historical predecessor material and alpha.2 traces are provenance/regression evidence. They do not control the alpha.3 normative core.
