from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "network/CURRENT.aset"
NETWORK = ROOT / "network/alpha4/NETWORK.aset"
PROFILES = ROOT / "network/alpha4/profiles/PROFILES.aset"
ALPHA4_BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"
HISTORY = ROOT / "history/REFERENCES.aset"
EXPRESSION_ORACLE = ROOT / "theory/network-seed-reflection/EXPRESSION_ASSURANCE.json"
CITATION = ROOT / "CITATION.cff"

EXPECTED_ALPHA4_BINDING_SHA256 = "2d725c2f81fa7cb00f7eb24253184e33dd46fac863aed4f489ffde95ad7d92fb"
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_current_pointer() -> None:
    current = lines(CURRENT)
    required = {
        "ASET-NETWORK-CURRENT 1 ASET-NETWORK-ALPHA4 0.1.0-alpha.4",
        "SEMANTIC-PRECEDENCE NONE",
        "CURRENT-REPRESENTATION network/alpha4/NETWORK.aset",
        "CURRENT-PROFILES network/alpha4/profiles/PROFILES.aset",
        "CURRENT-UPSTREAM-BINDING upstream/ASET_SEED_ALPHA4_BINDING.aset",
        "HISTORICAL-PREDECESSOR history/REFERENCES.aset NETWORK-0.1.0-ALPHA.3",
        "INDEPENDENT-EXPRESSION-ORACLE theory/network-seed-reflection/EXPRESSION_ASSURANCE.json",
        "HISTORICAL-COMPATIBILITY NONE",
        "REFERENCE-ORACLE-AUTHORITY NONE",
        "PROMOTION-SEMANTIC-DELTA NONE",
        "CHECK CURRENT tools/validate_current_network.py",
        "GATE tools/alpha4_network_gate.py",
    }
    require(set(current) == required, "current representation pointer mismatch")


def validate_current_subjects() -> None:
    network = lines(NETWORK)
    profiles = lines(PROFILES)
    require(network[0] == "ASET-NETWORK 1 ASET-NETWORK-ALPHA4 alpha4", "Alpha4 subject mismatch")
    require("SEMANTIC-PRECEDENCE NONE" in network, "Alpha4 subject gained semantic precedence")
    require("ALPHA3-COMPATIBILITY NONE" in network, "Alpha4 compatibility boundary changed")
    require(
        profiles[0] == "ASET-NETWORK-PROFILES 1 ASET-NETWORK-ALPHA4-PROFILES alpha4",
        "Alpha4 profile registry mismatch",
    )
    require("SEMANTIC-PRECEDENCE NONE" in profiles, "profile registry gained precedence")
    require("ALPHA3-COMPATIBILITY NONE" in profiles, "profile compatibility boundary changed")
    require(sha256(ALPHA4_BINDING) == EXPECTED_ALPHA4_BINDING_SHA256, "Alpha4 Seed binding drift")


def validate_history_boundary() -> None:
    history = HISTORY.read_text(encoding="utf-8")
    required = (
        "STATE NETWORK-0.1.0-ALPHA.3",
        "TAG v0.1.0-alpha.3",
        f"COMMIT {EXPECTED_ALPHA3_RELEASE_COMMIT}",
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
    require(EXPRESSION_ORACLE.is_file(), "independent expression oracle profile missing")


def validate_project_identity() -> None:
    citation = CITATION.read_text(encoding="utf-8")
    require('version: "0.1.0-alpha.4"' in citation, "citation version is not Alpha4")
    require("family-names: Prychyna" in citation, "citation author family name drift")
    require("given-names: Dzmitry" in citation, "citation author given name drift")
    require("https://github.com/attractor-set/aset-network" in citation, "repository locator drift")


def main() -> int:
    validate_current_pointer()
    validate_current_subjects()
    validate_history_boundary()
    validate_project_identity()
    print("ASET_NETWORK_CURRENT_REPRESENTATION=ASET-NETWORK-ALPHA4")
    print("ASET_NETWORK_CURRENT_PROJECT_VERSION=0.1.0-alpha.4")
    print("ASET_NETWORK_CURRENT_POINTER_SEMANTIC_PRECEDENCE=NONE")
    print("ASET_NETWORK_ALPHA3_PREDECESSOR=HISTORICAL_REFERENCE")
    print("ASET_NETWORK_ALPHA3_COMPATIBILITY_INHERITED=false")
    print("ASET_NETWORK_REFERENCE_ORACLE_AUTHORITY=false")
    print("ASET_NETWORK_PROMOTION_SEMANTIC_DELTA=NONE")
    print("ASET_NETWORK_CURRENT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
