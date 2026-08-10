# ADR-002: Minimal alpha boundary

Status: **Superseded by the 0.1.0-alpha.3 minimal-admission cutover.** This ADR is retained as historical decision evidence; current normative scope is defined by `extension/canonical/source/network-extension-model.json`.

## Decision

Version 0.1 alpha defines federation identity, membership, exact routes, export, import observation, local recognition, route suspension and withdrawal. Transport, consensus, cryptography, HE, partitions and reconciliation are deferred.

## Rationale

This keeps the extension testable against ASET Seed without turning it into a second universal system canon.
