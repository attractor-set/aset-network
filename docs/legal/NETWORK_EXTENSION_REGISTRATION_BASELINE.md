# Network Extension registration / deposit baseline

Status: **non-normative release procedure**.

Use this checklist after a material release has been merged, formally verified,
and frozen. Do not create a legal baseline from an unmerged working branch when a
release commit can be used instead.

## 1. Freeze prerequisites

Required before producing the baseline:

- release candidate is on the intended release commit;
- tracked worktree is clean;
- deterministic canon projection check passes;
- canon package validation passes;
- conformance tests pass;
- TLC safety passes;
- TLC history passes;
- TLC conditional Federation Profile liveness passes when that optional claim is included;
- canon -> Network TLAPS refinement/equivalence gate passes;
- Network -> pinned Seed TLAPS refinement gate passes;

For `0.1.0-alpha.3`, the expected assurance shape is:

```text
Network machine-readable alpha.3 canon
        |
        v
NetworkCanonProjection.tla
        | TLAPS 3/3
        v
minimal NetworkExtension.tla
        | TLAPS 35/35
        v
pinned SeedResolution.tla
```

TLC safety/history and optional Federation Profile liveness are separate bounded assurance surfaces and do not replace TLAPS.

## 2. Frozen identity record

Record the following from the exact release tree:

```text
WORK_TITLE=
RELEASE=
REPOSITORY=
COMMIT=
TREE=
TAG=
LICENSE=

CANON_PACKAGE_DIGEST=
FORMAL_RELATION_DIGEST=
NETWORK_CANON_PROJECTION_SHA256=
NETWORK_CANON_REFINEMENT_PROOF_SHA256=
NETWORK_SEED_REFINEMENT_PROOF_SHA256=

NETWORK_CANON_REFINEMENT_STATUS=MECHANICALLY_PROVED
NETWORK_CANON_REFINEMENT_OBLIGATIONS=
NETWORK_SEED_REFINEMENT_STATUS=MECHANICALLY_PROVED
NETWORK_SEED_REFINEMENT_OBLIGATIONS=

PINNED_SEED_RELEASE_COMMIT=
PINNED_SEED_RESOLUTION_SHA256=
TLAPM_COMMIT=
TLAPM_VERSION=

INPI_DEPOSIT_SHA256=
```

The obligation counts are evidence about the frozen proof artifacts. They are not
part of the normative semantics and may change if a proof is refactored without a
semantic change.

`INPI_DEPOSIT_SHA256` intentionally uses the same identifier as the ASET Seed
deposit tooling. It identifies the deterministic deposit snapshot, not the
normative canon package or the formal-relation digest.

## 3. Deposit content

Prefer a human-reviewable deposit package containing:

1. title page identifying the work and release;
2. short description of the Network Extension and its relationship to ASET Seed;
3. normative machine-readable canon in a preserved representation;
4. normative prose needed to understand the work;
5. formal-assurance overview;
6. frozen identity record from section 2;
7. file inventory and SHA-256 manifest;
8. license notice;
9. authorship/rightsholder declaration prepared for the filing process.

Do not describe TLA+ assurance modules as replacing the normative machine-readable
canon. They are evidence/projections of the frozen work.

## 4. Suggested work description

A concise filing description may state:

> ASET Network Extension is a separately versioned normative extension in the ASET
> specification family. Its universal core defines only target-local admission of
> foreign evidence; federation lifecycle is an optional Seed-bound profile and
> terminal recognition remains target-local Seed-owned. The deposited release
> includes a machine-readable normative canon and formal
> assurance artifacts that mechanically relate the generated canon projection to
> the handwritten Network behavioral model and the Network model to the pinned
> Seed formal model.

Adjust filing-language terminology to the actual form and jurisdiction. Do not use
this suggested text to claim a legal category that the filing authority does not
accept.

## 5. After filing

Store privately or in the appropriate project records:

- filing/request number;
- filing date;
- certificate or official receipt when issued;
- exact deposit-package SHA-256;
- exact release commit/tree/tag;
- any executed assignment or representation document relevant to titularity.

Do not publish personal identifiers, residential addresses, signatures, identity
documents, or filing credentials in the public repository.

## 6. Later versions

A new filing is not automatically required for every subsequent release. Consider
another baseline when a release contains a material new body of protected
expression, a major architectural rewrite, a transfer of titularity, or another
change for which a new official evidentiary record is useful.
