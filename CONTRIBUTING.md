# Contributing

ASET Network Alpha4 is the current public representation selected by
`network/CURRENT.aset`.

Changes to current Alpha4 semantic subjects require, as applicable:

1. an explicit subject/binding change;
2. corresponding independent operational and relational expression changes;
3. updated pairing or boundary proofs and executable gates;
4. preservation of state/transition/Authority ownership boundaries;
5. an explicit statement about the content-addressed ASET Seed 0.4alpha boundary;
6. passing `python -m tools.alpha4_network_gate`, the Alpha4 TLAPS/TLC gates,
   `python -m pytest -q`, and formatting/lint checks.

Operational Forth, relational TLA, proofs and `network/CURRENT.aset` do not gain
semantic precedence merely by representing, verifying or selecting a subject.

`extension/canonical/**` is the frozen Alpha3 predecessor surface. Current
Alpha4 work must preserve it unless a change is explicitly scoped as historical
predecessor maintenance. The Python code under `reference/` is non-normative
historical conformance machinery and is not a current semantic oracle.
