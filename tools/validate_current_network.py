from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "network/CURRENT.aset"
NETWORK = ROOT / "network/alpha4/NETWORK.aset"
PROFILES = ROOT / "network/alpha4/profiles/PROFILES.aset"
ALPHA4_BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"
ALPHA3_BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"
ALPHA3_PACKAGE = ROOT / "extension/canonical/CANON_PACKAGE.json"

EXPECTED_ALPHA3_PACKAGE_DIGEST = (
    "sha256:82976c30880ed2a6c810b8f0aa5585dee5ab73fa12684a9d17784bac0a1bbbc7"
)
EXPECTED_ALPHA3_BINDING_SHA256 = "a40002343d3f2a4ed9af2d2bbefb9cfbee7282b62aefca04e6a5bbaadf433a68"
EXPECTED_ALPHA4_BINDING_SHA256 = "2d725c2f81fa7cb00f7eb24253184e33dd46fac863aed4f489ffde95ad7d92fb"


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
        "FROZEN-PREDECESSOR extension/canonical/CANON_PACKAGE.json",
        "FROZEN-PREDECESSOR-COMPATIBILITY NONE",
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


def validate_frozen_predecessor() -> None:
    package = json.loads(ALPHA3_PACKAGE.read_text(encoding="utf-8"))
    require(
        package["canon_id"] == "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3",
        "Alpha3 predecessor canon identity drift",
    )
    require(
        package["package_digest"] == EXPECTED_ALPHA3_PACKAGE_DIGEST,
        "Alpha3 predecessor package digest drift",
    )
    require(sha256(ALPHA3_BINDING) == EXPECTED_ALPHA3_BINDING_SHA256, "Alpha3 binding drift")
    require(sha256(ALPHA4_BINDING) == EXPECTED_ALPHA4_BINDING_SHA256, "Alpha4 Seed binding drift")


def validate_project_metadata() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    require(metadata["project"]["name"] == "aset-network", "project name drift")
    require(metadata["project"]["version"] == "0.1.0a4", "project version is not Alpha4")


def main() -> int:
    validate_current_pointer()
    validate_current_subjects()
    validate_frozen_predecessor()
    validate_project_metadata()
    print("ASET_NETWORK_CURRENT_REPRESENTATION=ASET-NETWORK-ALPHA4")
    print("ASET_NETWORK_CURRENT_PROJECT_VERSION=0.1.0-alpha.4")
    print("ASET_NETWORK_CURRENT_POINTER_SEMANTIC_PRECEDENCE=NONE")
    print("ASET_NETWORK_ALPHA3_PREDECESSOR=FROZEN")
    print("ASET_NETWORK_ALPHA3_COMPATIBILITY_INHERITED=false")
    print("ASET_NETWORK_REFERENCE_ORACLE_AUTHORITY=false")
    print("ASET_NETWORK_PROMOTION_SEMANTIC_DELTA=NONE")
    print("ASET_NETWORK_CURRENT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
