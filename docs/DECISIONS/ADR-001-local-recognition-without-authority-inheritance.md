# ADR-001: Local recognition without authority inheritance

## Decision

Cross-context communication is modeled as evidence transfer followed by target-local ASET Seed resolution. Federation membership, ancestry, routing and source-side decisions do not create Resolution Authority in the target Context.

## Consequence

There is no global acceptance bit. Different Contexts may validly recognize the same exported artifact differently under their own Constitutions and policy epochs.
