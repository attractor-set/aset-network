# Contributing

Changes to normative files require:

1. a machine-readable model change;
2. positive and negative conformance cases;
3. updated package hashes;
4. passing `python -m pytest -q` and `python -m tools.validate_extension`;
5. an explicit compatibility statement against the pinned ASET Seed package.

Normative meaning is defined by `extension/canonical/`, not by the Python reference model.
