from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from tools.validate_repository_minimal import repository_paths

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "network/alpha4/NETWORK.aset"
PROFILES = ROOT / "network/alpha4/profiles/PROFILES.aset"
BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"
HISTORY = ROOT / "history/REFERENCES.aset"
CITATION = ROOT / "CITATION.cff"

EXPECTED_ALPHA4_BINDING_SHA256 = "21fedbba98b1c36d96dba2072ccaf2e088348be13a1c9ea8d5e3bdf7616d27a4"
EXPECTED_SEED_ALPHA4_RELEASE_TAG = "seed-0.4alpha-3way"
EXPECTED_ALPHA3_PACKAGE_DIGEST = (
    "sha256:82976c30880ed2a6c810b8f0aa5585dee5ab73fa12684a9d17784bac0a1bbbc7"
)
EXPECTED_ALPHA3_PACKAGE_SHA256 = (
    "sha256:2ffdc36311eda6fe18d1ac896f8b4a532b52b3b7ccc58adc4c0560a1db5a6463"
)
EXPECTED_ALPHA3_RELEASE_COMMIT = "45cdac43e3d07989c21cbb3a46d82b1908354e27"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_active_selection() -> None:
    children = {path.split("/", 2)[1] for path in repository_paths() if path.startswith("network/")}
    require(children == {"alpha4"}, f"Network active-line surface drift: {sorted(children)}")
    require(NETWORK.is_file(), "Alpha4 subject missing")
    require(PROFILES.is_file(), "Alpha4 profile registry missing")


def validate_network_surface() -> None:
    network = lines(NETWORK)
    profiles = lines(PROFILES)
    required = (
        "ASET-NETWORK 1 ASET-NETWORK-ALPHA4 alpha4",
        "SEMANTIC-PRECEDENCE NONE",
        "ALPHA3-COMPATIBILITY NONE",
        "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA",
        "SEED-EXTENSION-BIND OPERATIONAL OBSERVE-UNKNOWN ADMIT-FRESH,ADMIT-REPLAY",
        "SEED-EXTENSION-BIND RELATIONAL ObserveUnknown AdmitFresh,AdmitReplay",
        "SEED-EXTENSION-BIND CAUSAL OBSERVE-UNKNOWN ADMIT-FRESH,ADMIT-REPLAY",
        "STATE IMPORTS SET-OF-EXACT-IMPORT-OBSERVATIONS",
        "TRANSITION ADMIT-IMPORT",
        "SEED-PROJECTION ADMIT-IMPORT OBSERVE-UNKNOWN",
        "SEED-RECOGNITION-OWNER TARGET-LOCAL-SEED",
        "EFFECT-PERMITTED-BY-NETWORK NEVER",
        "CAUSAL-MODEL network/alpha4/causal/components.petri",
    )
    for declaration in required:
        require(declaration in network, f"Network Alpha4 declaration missing: {declaration}")
    require(
        "ALLOW" not in network and "BLOCK" not in network,
        "Network contains terminal recognition state",
    )

    require(
        profiles[0] == "ASET-NETWORK-PROFILES 1 ASET-NETWORK-ALPHA4-PROFILES alpha4",
        "Alpha4 profile registry mismatch",
    )
    require("SEMANTIC-PRECEDENCE NONE" in profiles, "profile registry gained precedence")
    require("ALPHA3-COMPATIBILITY NONE" in profiles, "profile compatibility boundary changed")
    require(
        sha256_hex(BINDING) == EXPECTED_ALPHA4_BINDING_SHA256,
        "Alpha4 Seed binding drift",
    )

    forth = (ROOT / "network/alpha4/operational/components.forth").read_text(encoding="utf-8")
    require(forth.count(";") == 3, "Network Alpha4 operational expression must have 3 words")
    require(
        "LOCAL-ALLOW!" not in forth and "LOCAL-BLOCK!" not in forth,
        "Network operational expression contains Seed-local authority operation",
    )
    causal = ROOT / "network/alpha4/causal/components.petri"
    require(causal.is_file(), "Network causal representation missing")
    causal_text = causal.read_text(encoding="utf-8")
    require("SEMANTIC-PRECEDENCE NONE" in causal_text, "Network causal precedence drift")
    require(causal_text.count("TRANSITION ") == 3, "Network causal component count drift")
    require(
        len([line for line in network if line.startswith("CAUSAL-BIND ")]) == 3,
        "Network causal binding count drift",
    )


def validate_history_boundary() -> None:
    history = HISTORY.read_text(encoding="utf-8")
    required = (
        "STATE NETWORK-0.1.0-ALPHA.3",
        "TAG v0.1.0-alpha.3",
        f"COMMIT {EXPECTED_ALPHA3_RELEASE_COMMIT}",
        "IDENTITY NETWORK-0.1.0-ALPHA.3 CANON-ID ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3",
        f"DIGEST NETWORK-0.1.0-ALPHA.3 CANON-PACKAGE {EXPECTED_ALPHA3_PACKAGE_DIGEST}",
        f"DIGEST NETWORK-0.1.0-ALPHA.3 CANON-PACKAGE-BYTES {EXPECTED_ALPHA3_PACKAGE_SHA256}",
        "RELATION ASET-NETWORK-ALPHA4 HISTORICAL_PREDECESSOR NETWORK-0.1.0-ALPHA.3",
        "COMPATIBILITY ASET-NETWORK-ALPHA4 NETWORK-0.1.0-ALPHA.3 NONE",
        (
            "PROOF NETWORK-0.1.0-ALPHA.3 SEED-REFLECTION "
            "ASET-NETWORK-SEED-REFINEMENT-TLAPS-V2 35 MECHANICALLY_PROVED"
        ),
    )
    for marker in required:
        require(marker in history, f"history reference missing: {marker}")


def validate_project_identity() -> None:
    citation = CITATION.read_text(encoding="utf-8")
    require('version: "0.1.0-alpha.4"' in citation, "citation version is not Alpha4")
    require("family-names: Prychyna" in citation, "citation author family name drift")
    require("given-names: Dzmitry" in citation, "citation author given name drift")
    require(
        "https://github.com/attractor-set/aset-network" in citation,
        "repository locator drift",
    )


def parse_binding() -> dict[str, str]:
    binding_lines = lines(BINDING)
    require(
        binding_lines[0] == "ASET-SEED-BINDING 1 ASET-SEED-0.4-ALPHA CONTENT-ADDRESSED",
        "Seed Alpha4 binding header mismatch",
    )
    sources: dict[str, str] = {}
    for line in binding_lines:
        if line.startswith("SOURCE "):
            _, path, digest = line.split()
            require(path not in sources, f"duplicate bound source: {path}")
            require(re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None, "bad digest")
            sources[path] = digest
    expected_sources = {
        "seed/alpha4/SEED.aset",
        "seed/alpha4/operational/components.forth",
        "seed/alpha4/formal/RestrictedOperationalSemantics.tla",
        "seed/alpha4/formal/ComponentRelations.tla",
        "seed/alpha4/formal/OperationalRelationalPairingProofs.tla",
        "seed/alpha4/formal/ComponentCompositionProofs.tla",
        "seed/alpha4/causal/components.petri",
        "theory/local-recognition/formal/LocalRecognitionAlgebra.tla",
    }
    require(set(sources) == expected_sources, "Seed Alpha4 bound source surface mismatch")
    require(
        f"RELEASE-TAG {EXPECTED_SEED_ALPHA4_RELEASE_TAG}" in binding_lines,
        "Seed Alpha4 release locator mismatch",
    )
    for declaration in (
        "RELEASE-TREE sha256:136e174a987ee961877472eecac3903e4f1e54a68059815e9b84e8fb966e00cc",
        "PROFILE-TREE sha256:fb75339485027ad1529714e1793669c4850390fe54a586864772a13ab90c094e",
        (
            "COMPANION ENGLISH en/Seed.md "
            "sha256:8d44ddd7d244b385de5e37bd9429f9509680775593330a258f97ff178c5fb7b9"
        ),
        (
            "COMPANION PYTHON python/aset_seed_alpha4.py "
            "sha256:fb71c154b8e6ee05986b6d203852ea1a964176ecb4e9753a51119dcbb9332071"
        ),
        "ASSURANCE-BASE OPERATIONAL seed/alpha4/operational/components.forth OBSERVE-UNKNOWN",
        "ASSURANCE-BASE RELATIONAL seed/alpha4/formal/ComponentRelations.tla ObserveUnknown",
        "ASSURANCE-BASE CAUSAL seed/alpha4/causal/components.petri OBSERVE-UNKNOWN",
    ):
        require(
            declaration in binding_lines,
            f"Seed extension binding declaration missing: {declaration}",
        )
    require(
        "REQUIRED-SEED-PAIR ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN "
        "ObserveUnknown ObserveUnknownPairing" in binding_lines,
        "Seed OBSERVE-UNKNOWN pairing requirement missing",
    )
    require(
        "REQUIRED-SEED-CAUSAL-BIND ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN" in binding_lines,
        "Seed OBSERVE-UNKNOWN causal binding requirement missing",
    )
    require(
        "NETWORK-PROJECTION ADMIT-IMPORT OBSERVE-UNKNOWN" in binding_lines,
        "Network-to-Seed projection declaration missing",
    )
    return sources


def validate_seed_root(seed_root: Path, sources: dict[str, str]) -> None:
    for relative, expected in sources.items():
        path = seed_root / relative
        require(path.is_file(), f"bound Seed source missing: {relative}")
        require(sha256(path) == expected, f"bound Seed source digest mismatch: {relative}")
    seed = (seed_root / "seed/alpha4/SEED.aset").read_text(encoding="utf-8")
    require(
        seed.startswith("ASET-SEED 1 ASET-SEED-0.4-ALPHA 0.4alpha\n"),
        "Seed Alpha4 subject identity mismatch",
    )
    require(
        "PAIR ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN ObserveUnknown "
        "ObserveUnknownPairing" in seed,
        "Seed Alpha4 OBSERVE-UNKNOWN pair unavailable",
    )
    require(
        "CAUSAL-BIND ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN" in seed,
        "Seed Alpha4 OBSERVE-UNKNOWN causal binding unavailable",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path)
    args = parser.parse_args()

    validate_active_selection()
    validate_network_surface()
    validate_history_boundary()
    validate_project_identity()
    sources = parse_binding()

    print("ASET_NETWORK_CURRENT_REPRESENTATION=ASET-NETWORK-ALPHA4")
    print("ASET_NETWORK_CURRENT_PROJECT_VERSION=0.1.0-alpha.4")
    print("ASET_NETWORK_CURRENT_SELECTION=UNIQUE_ACTIVE_NETWORK_LINE")
    print("ASET_NETWORK_ALPHA3_PREDECESSOR=HISTORICAL_REFERENCE")
    print("ASET_NETWORK_ALPHA3_COMPATIBILITY_INHERITED=false")
    print("ASET_NETWORK_CURRENT_VALIDATION=PASS")

    if args.seed_root is not None:
        validate_seed_root(args.seed_root.resolve(), sources)
        print("ALPHA4_NETWORK_SEED_CONTENT_BINDING=PASS")
        print("ALPHA4_NETWORK_SEED_ASSURANCE_BINDINGS=OPERATIONAL,RELATIONAL,CAUSAL")
    else:
        print("ALPHA4_NETWORK_SEED_CONTENT_BINDING=DECLARED")
        print("ALPHA4_NETWORK_SEED_ASSURANCE_BINDINGS=DECLARED")
    print("ALPHA4_NETWORK_SINGLE_STATE=IMPORTS")
    print("ALPHA4_NETWORK_SINGLE_TRANSITION=ADMIT-IMPORT")
    print("ALPHA4_NETWORK_TERMINAL_RECOGNITION_STATE=ABSENT")
    print("ALPHA4_NETWORK_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
