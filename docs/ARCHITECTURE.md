# Architecture

## Sovereignty boundary

Each member is an independent Context with its own Constitution, Authority, canonical state and policy epoch. The federation stores composition and routing facts; it does not become an Authority for member-local decisions.

## Recognition pipeline

1. The source Context emits a content-addressed Export under an exact active RouteGrant.
2. The target Context records an ImportObservation as `UNKNOWN/BLOCKED`.
3. The target opens or binds an ASET Seed resolution cycle using its own ContextBinding and ResolutionAuthority.
4. A terminal Seed result is recorded as a local RecognitionReceipt.
5. Only target-local `ACCEPT/ALLOW` can authorize a later effect. Effect execution is outside this extension.

## Metafederation

A metafederation is a graph or composition of federations. It does not imply a root Context, a global Constitution or inherited Resolution Authority. Cross-federation recognition repeats the same local pipeline at every sovereign boundary.


## Dynamic profiles without a second decision algebra

`ASET-NETWORK-DYNAMIC-PROFILES-V1` is an optional normative profile surface. It does not extend the Network semantic state and does not add Network transition kinds. A `ProfileDefinition` is immutable, content-addressed external evidence. A `ProfileBinding` immutably binds one exact profile digest to one target Context, target state root, target policy epoch and Seed scope. It contains no resolution identifier or activation status.

Profile availability, transport, cryptographic verification, remote recognition and network observation do **not** activate a profile. For activation, the binding is projected directly into a Seed `ResolutionBinding`: target Context → `context_id`, target state root → `state_root`, profile digest → `question_digest`, target policy epoch → `policy_epoch`, and declared Seed scope → `scope`. A fresh Seed `resolution_id` is then used. Applicability is derived only when that exact target-local Seed resolution evaluates `ALLOW`. There is therefore no normative `active_profiles` registry and no second profile decision algebra. A changed definition has a different digest and requires a new exact binding; an earlier `ALLOW` does not carry forward.

Profiles may strengthen the parent contract but may not weaken it or supersede Seed. The Network core deliberately defines no universal profile dependency resolver, precedence system, composition algebra, negotiation protocol or runtime plugin lifecycle. A composed profile is responsible for its own constraints and refinement evidence.

This keeps profile dynamism in immutable evidence plus local recognition rather than in mutable Network semantics:

```text
ProfileDefinition --digest--> ProfileBinding --projection--> Seed ResolutionBinding
                                                         UNKNOWN / ALLOW / BLOCK
```

## Formal assurance boundary

The normative source is the machine-readable Network Extension canon. The TLA+ modules are assurance projections bound by `extension/canonical/formal/canon-tla-relation.json`.

Safety is checked independently from liveness. `SafetySpec` permits route suspension and member withdrawal while preserving local authority, local recognition, fail-closed import semantics and the absence of an implicit superior Context.

`FairSpec` adds the assumptions from `ASET-NETWORK-LIVENESS-V1`: retained delivery, target observation and local resolution are weakly fair, and the target needed for the claimed progress is not permanently removed. The resulting guarantee is eventual terminal **local** resolution, not eventual `ACCEPT`.

`EventuallyDelivered`, `EventuallyObserved` and `EventuallyResolved` are therefore not conjectures in this assurance profile. `NetworkExtensionLiveness.cfg` asks TLC to check them under `FairSpec` for the configured finite model. A passing TLC run establishes the properties for that bounded state space under those fairness assumptions; it is neither an unconditional transport guarantee nor an unbounded theorem for arbitrary Context or artifact cardinality.

The finite TLC configurations use `CHECK_DEADLOCK FALSE` because terminal safety states (for example, all members withdrawn) and finite-model exhaustion are legitimate quiescent states. This is not a waiver of progress checking: `NoUnexpectedSafetyDeadlock` rejects non-terminal safety deadlocks, `NoPendingProgressDeadlock` together with the liveness properties rejects a quiescent state that still carries an unresolved delivery/import/resolution obligation, and `NoUnexpectedHistoryDeadlock` accepts only exhaustion of the bounded history-digest universe.

### State/trace separation

The machine-readable canon classifies semantic network state and canonical evidence history as distinct normative surfaces. `state_partition.semantic_state_fields` contains the fields projected into the main state machine; `state_partition.evidence_history_fields` contains the append-only evidence trace. Evidence history does not itself confer Authority or change transition eligibility unless an explicit normative rule references a prior transition.

`NetworkExtension.tla` contains only semantic network state needed by sovereignty, routing, import/recognition and liveness properties. It does not carry the complete ordered execution history: including that sequence prevents TLC from merging execution permutations that reach the same semantic state and creates factorial state-space growth. `inTransit` is deliberately monotonic inside this assurance state: membership records that transport was initiated, while `delivered` separately records successful delivery; it is not a pending-message queue. Likewise, `authorityOwner` is an explicit sovereignty witness and `superiorContexts` is an always-empty sentinel for the no-super-context invariant. Neither field is a placeholder for a future federation-wide Authority hierarchy. `NetworkHistory.tla` is a separate bounded trace projection for `NET-INV-010`; it checks that every accepted transition appends exactly one fresh opaque history digest and that the pre-existing sequence remains a prefix. This separation therefore mirrors an explicit canon partition rather than merely being a model-checking optimization.

### Core conformance and liveness claim

`ASET-NETWORK-EXTENSION-CONFORMANCE-V1` is the core conformance profile. `ASET-NETWORK-LIVENESS-V1` is a separate optional normative capability claim: an implementation can conform to the core without making a liveness claim. If it does claim liveness, it must declare the required assumptions and may claim only the guarantees that hold while those assumptions hold.

## Seed refinement boundary

`NetworkExtensionSeedProjection.tla` projects each target Context to the Seed-compatible observable resolution algebra: unresolved imports are `UNKNOWN/BLOCKED`, local acceptance is `ACCEPT/ALLOW`, and local denial is `DENY/BLOCKED`. Network actions never transfer `authorityOwner`.

`NetworkExtensionSeedRefinement.tla` adds the explicit refinement mapping to the exact pinned upstream `SeedResolution.tla`. In that mapping, each imported export is a Seed `ResolutionId`, the target-scoped pair `(target Context, artifact)` is the abstract Seed `Binding`, and the target Context is the abstract target-local `Authority`. `Observe` maps to `RegisterRequest`; local `ResolveAccept` and `ResolveDeny` map to `SubmitResolution(..., ALLOW)` and `SubmitResolution(..., BLOCK)` respectively; route, export, delivery, suspension, membership and withdrawal actions stutter at the Seed state boundary. The mapping always uses `NoCommitment` and projects no Seed conflict observation.

The Context-to-Authority and artifact-to-Binding identifications are assurance abstractions, not concrete identity claims. The actual upstream `SeedResolution.tla` is not vendored into the Network canon. `tools/run_seed_refinement_tlaps.py` loads it from a separately supplied ASET checkout, verifies the exact SHA-256 pinned to Seed release `seed-0.3.0-alpha.3`, and only then invokes TLAPS. A missing module, wrong Seed commit, or SHA-256 mismatch is a hard pre-proof failure rather than a warning or a substituted proof target. `NetworkExtensionSeedRefinementProofs.tla` contains the behavioral and evaluator theorems, and the pinned proof gate has mechanically proved all 261 obligations. `extension/canonical/assurance/seed-refinement-proof.json` binds that result to the exact Network mapping/proof artifacts, Seed source and TLAPM commit; the obligation count is recorded evidence rather than a semantic invariant. `canon-tla-relation.json` therefore records the pinned refinement status as `MECHANICALLY_PROVED`.


### Formal release gate

`tools/run_formal_release_gate.py` is the aggregate release-time formal gate. It requires repository diff hygiene, rebuilds the canonical package, validates the canon, runs black-box conformance and tests, saturates the three TLC assurance models, and reruns the pinned Seed TLAPS refinement proof. A release-formal pass is emitted only if every stage succeeds on the same working tree. The generated `dist/formal-release-gate.json` is runtime evidence and is not itself part of the normative canon.
