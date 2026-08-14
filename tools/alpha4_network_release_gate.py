from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "dist/ASET-Network-0.1.0-alpha.4"
PROFILES = "dist/ASET-Network-0.1.0-alpha.4-profiles"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--seed-release-root", type=Path, required=True)
    parser.add_argument("--seed-profiles-root", type=Path, required=True)
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    commands = [
        [sys.executable, "-m", "tools.alpha4_network_gate"],
        [
            sys.executable,
            "-m",
            "tools.validate_alpha4_network",
            "--seed-root",
            str(args.seed_root),
        ],
        [
            sys.executable,
            "-m",
            "tools.alpha4_network_seed_extension",
            "--seed-root",
            str(args.seed_root),
            "--seed-profiles-root",
            str(args.seed_profiles_root),
        ],
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "tools.run_alpha4_network_tlaps", "--tlapm", args.tlapm],
        [sys.executable, "-m", "tools.run_alpha4_network_profile_tlaps", "--tlapm", args.tlapm],
        [sys.executable, "-m", "tools.run_alpha4_network_profile_tlc"],
        [
            sys.executable,
            "-m",
            "tools.build_alpha4_network_release",
            "--seed-release-root",
            str(args.seed_release_root),
            "--seed-profiles-root",
            str(args.seed_profiles_root),
            "--verify-determinism",
        ],
        [
            sys.executable,
            "-m",
            "tools.run_alpha4_network_release_tlaps",
            "--release-root",
            RELEASE,
            "--seed-release-root",
            str(args.seed_release_root),
            "--tlapm",
            args.tlapm,
            "--output",
            "dist/network-release-assembled-tlaps-evidence.json",
        ],
        [
            sys.executable,
            "-m",
            "tools.alpha4_network_expression_airgap",
            "--profiles-root",
            PROFILES,
            "--output",
            "dist/network-python-airgap-evidence.json",
        ],
        [
            sys.executable,
            "-m",
            "tools.alpha4_network_release_admission",
            "--release-root",
            RELEASE,
            "--profiles-root",
            PROFILES,
            "--proof-evidence",
            "dist/network-release-assembled-tlaps-evidence.json",
            "--airgap-evidence",
            "dist/network-python-airgap-evidence.json",
            "--release-archive",
            RELEASE + ".zip",
            "--profiles-archive",
            PROFILES + ".zip",
            "--output",
            "dist/network-release-admission-certificate.json",
        ],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "ruff", "check", "."],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            print("ALPHA4_NETWORK_RELEASE_GATE=FAIL")
            return result.returncode
    print("ALPHA4_NETWORK_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
