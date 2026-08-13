from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_FORMAL = ROOT / "network/alpha4/formal"
DYNAMIC_FORMAL = ROOT / "network/alpha4/profiles/dynamic/formal"
FEDERATION_FORMAL = ROOT / "network/alpha4/profiles/federation/formal"
LIVENESS_FORMAL = ROOT / "network/alpha4/profiles/liveness/formal"
COMPOSITION_RELATIONAL = ROOT / "network/alpha4/profiles/composition/federation-liveness/formal"
COMPOSITION_FORMAL = ROOT / "network/alpha4/profiles/composition/federation-liveness/assurance"

MODULES = [
    DYNAMIC_FORMAL / "DynamicOperationalRelationalPairingProofs.tla",
    DYNAMIC_FORMAL / "DynamicProfileBoundaryProofs.tla",
    FEDERATION_FORMAL / "FederationOperationalRelationalPairingProofs.tla",
    FEDERATION_FORMAL / "NetworkStutteringProofs.tla",
    LIVENESS_FORMAL / "LivenessOperationalRelationalPairingProofs.tla",
    LIVENESS_FORMAL / "LivenessBoundaryProofs.tla",
    COMPOSITION_RELATIONAL / "FederationLivenessOperationalRelationalPairingProofs.tla",
    COMPOSITION_FORMAL / "FederationLivenessContractProofs.tla",
]
INCLUDE_DIRS = [
    CORE_FORMAL,
    DYNAMIC_FORMAL,
    FEDERATION_FORMAL,
    LIVENESS_FORMAL,
    COMPOSITION_RELATIONAL,
    COMPOSITION_FORMAL,
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    total = 0
    for module in MODULES:
        command = [args.tlapm]
        for directory in INCLUDE_DIRS:
            command.extend(["-I", str(directory)])
        command.append(str(module))
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        print(result.stdout, end="")
        if result.returncode:
            print(f"ALPHA4_NETWORK_PROFILE_TLAPS_MODULE={module.name} FAIL")
            return result.returncode
        matches = re.findall(r"All ([0-9]+) obligations? proved\.", result.stdout)
        if not matches:
            print(f"ALPHA4_NETWORK_PROFILE_TLAPS_MODULE={module.name} SUMMARY_MISSING")
            return 1
        count = int(matches[-1])
        total += count
        print(f"ALPHA4_NETWORK_PROFILE_TLAPS_MODULE={module.name} OBLIGATIONS={count} PASS")
    print(f"ALPHA4_NETWORK_PROFILE_TLAPS_OBLIGATIONS={total} PASS")
    print("ALPHA4_NETWORK_PROFILE_TLAPS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
