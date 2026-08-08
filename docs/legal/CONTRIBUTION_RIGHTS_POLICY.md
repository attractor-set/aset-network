# Contribution rights policy

Status: **non-normative project administration**.

This document exists to prevent technical contribution workflows from silently
changing the project's rights chain.

## 1. General rule

A Git commit, pull request, review approval, or merge does not by itself prove a
copyright assignment.

The project must distinguish:

- permission to use a contribution under the repository license;
- contributor authorship/copyright ownership;
- any patent license created by the applicable license;
- any separate assignment or CLA;
- trademark rights, which are not transferred merely by contributing code or text.

## 2. DCO is provenance, not assignment

A Developer Certificate of Origin / `Signed-off-by` process may be used to record
that a contributor has the right to submit a contribution under the project's
license.

It must **not** be described as transferring copyright ownership to the project or
to a maintainer. If centralized ownership is required, use an explicit written
assignment or an appropriately drafted contributor agreement.

## 3. Normative specification contributions

Changes to any normative canon, normative requirement, normative schema, or other
material specification surface require a stronger rights review than ordinary
implementation patches.

Before accepting a substantive third-party normative contribution, maintainers
must determine which of the following applies:

1. contributor retains ownership and licenses the contribution under the project's
   accepted terms; or
2. an executed CLA grants the project the additional rights required by governance;
   or
3. an executed assignment transfers the agreed rights.

The repository must not claim sole ownership of third-party normative expression
unless the rights chain actually supports that claim.

Until a project-approved contributor agreement/assignment process exists,
maintainers should avoid merging substantial third-party normative contributions
when centralized titularity is a release requirement.

## 4. Non-normative implementation contributions

Non-normative implementation and tooling contributions may ordinarily be accepted
under the repository license and the project's provenance process, subject to any
additional maintainer requirements.

Such contributions must not be represented as changing the normative ASET or
Network canon merely because they are merged into the same repository.

## 5. Patent-aware contribution handling

Where Apache License 2.0 applies, maintainers should remember that contributor
patent grants are governed by the license's patent provisions. A DCO does not
replace those provisions and is not a substitute for patent-specific legal review
when a contribution implicates material patent risk.

## 6. Trademark boundary

Contribution permission does not grant ownership of ASET names, logos, or marks.
Use of project marks remains subject to whatever trademark policy or registration
rights apply separately.

## 7. Required provenance records

For external contributions that are merged, preserve at minimum:

- contributor identity as represented in Git hosting records;
- commit identity;
- pull request identity;
- license/provenance declaration used for the contribution;
- any executed CLA/assignment identifier when one exists;
- review/merge record.

Do not place private agreement documents, signatures, government identifiers, or
other sensitive personal records in the public repository.

## 8. No retroactive assumption

If the contribution-rights process changes later, do not assume earlier
contributions are covered retroactively. Historical contributions must be evaluated
under the rights terms actually applicable when they were submitted or under a
later agreement that validly covers them.
