# ASET Network Extension — IP rights policy

Status: **non-normative project administration**.

This document records the intended separation of intellectual-property rights
around the ASET Network Extension. It does not alter the normative Network canon
or any formal assurance claim.

## 1. Separate rights layers

The project treats the following as distinct rights layers:

### 1.1 Specification and assurance materials

Original specification text, machine-readable source material, documentation,
formal models, proof modules, diagrams, and other original expression may be
protected by copyright independently of whether a voluntary registration is
obtained.

A voluntary registration or deposit is treated as **evidence of authorship,
titularity, date, and frozen content**, not as the source of the underlying
copyright.

The ASET Network Extension is treated as a separately versioned work in the ASET
specification family. Its relationship to ASET Seed is a dependency/refinement
relationship; it is not merged into the legal identity of the Seed release merely
because it refines Seed semantics.

### 1.2 Software implementations

Executable implementations, tooling, generators, validators, and other software
may be protected as computer programs separately from the specification itself.
A software-registration filing, where used, is an implementation-level measure
and does not redefine or supersede the normative specification.

### 1.3 Names and marks

Copyright in the specification does not by itself create the same rights as a
registered trademark. Rights in names, logos, and marks such as `ASET` are
managed separately from copyright registration and from repository licensing.

Unless expressly stated otherwise, no project document should be interpreted as
a transfer of trademark ownership.

### 1.4 Patent rights

Patent rights, if any, are distinct from copyright and trademark rights. The
presence of an open-source or open-specification license must not be described as
eliminating patent rights generally. Any patent effect is limited to the terms of
the applicable license and the claims actually covered by that license.

## 2. License does not equal transfer of ownership

Repository licensing grants permissions under the applicable license; it does
not by itself transfer copyright ownership in the underlying work.

Where Apache License 2.0 applies, its copyright and patent grants operate according
to that license. Trademark rights are not generally granted by the license beyond
the limited uses the license itself permits.

Accordingly, project documentation should distinguish:

- **ownership / authorship**;
- **permissions granted to recipients**;
- **patent licenses, where applicable**;
- **trademark rights**.

## 3. Network Extension as a separate registration baseline

A material frozen release of the Network Extension may receive its own voluntary
registration/deposit baseline rather than being treated merely as an amendment to
a Seed registration.

The baseline should identify at minimum:

- work title;
- release/version identifier;
- repository identity;
- exact Git commit and Git tree;
- normative canon package digest;
- canon/TLA relation digest;
- generated canon projection digest;
- proof/evidence artifact digests;
- pinned Seed release identity;
- pinned `SeedResolution.tla` digest;
- license identity;
- author/rightsholder information maintained outside the public repository when
  personal data should not be published.

## 4. Recommended Brazilian administrative separation

For a Brazil-based protection strategy, the project treats these as separate
administrative paths:

- literary/scientific/specification material: voluntary copyright registration
  through the Fundação Biblioteca Nacional / Escritório de Direitos Autorais;
- computer-program implementations: registration through INPI where useful;
- project name/logo and related marks: trademark filing through INPI where useful.

A filing decision is release- and strategy-specific. The repository does not
claim that every alpha, patch, implementation, or generated artifact requires a
new filing.

## 5. No automatic extension of an earlier registration

A prior registration/deposit of ASET Seed must not be described as automatically
covering later independently authored Network Extension content that was not part
of the deposited work.

For a material Network Extension milestone, the preferred evidentiary approach is
a separate frozen baseline that explicitly records its dependency on Seed.

## 6. Non-normative status

This policy is administrative. If it ever conflicts with:

1. applicable law;
2. an executed assignment, CLA, or other rights agreement;
3. the repository license;

those controlling instruments govern the rights question. None of those
instruments may silently redefine ASET Network normative semantics.
