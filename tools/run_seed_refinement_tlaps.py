#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
PROOF = FORMAL / "NetworkExtensionSeedRefinementProofs.tla"
BRIDGE = FORMAL / "NetworkExtensionSeedRefinement.tla"
EVID = ROOT / "extension/canonical/assurance/seed-refinement-proof.json"
BIND = ROOT / "upstream/ASET_SEED_BINDING.json"

VER = "4600b24"
COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
SEED_COMMIT = "633c130187b2a2bb42f24cfd66662d475de385d2"
SEED_SHA = "1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
THEOREMS = [
    "NetworkExtensionRefinesSeedSafetySpec",
    "NetworkProjectionMatchesSeedResolution",
]


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument("--seed-root", type=Path, default=Path.home() / "ASET")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-seed-refinement-proof.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    tlapm = args.tlapm.expanduser().resolve()
    seed_formal = args.seed_root.expanduser().resolve() / "seed/canonical/formal"
    seed = seed_formal / "SeedResolution.tla"
    errors: list[str] = []
    evidence = json.loads(EVID.read_text())
    binding = json.loads(BIND.read_text())

    if binding["seed_release_commit"] != SEED_COMMIT:
        errors.append("Seed release mismatch")
    if not seed.is_file() or h(seed) != SEED_SHA:
        errors.append("SeedResolution.tla digest mismatch")
    if evidence["proof_gate"]["final_theorems"] != THEOREMS:
        errors.append("theorem set mismatch")

    for path, key in [(BRIDGE, "mapping"), (PROOF, "proof")]:
        if evidence["network_artifacts"][key]["sha256"] != "sha256:" + h(path):
            errors.append(f"{key} digest mismatch")

    if not tlapm.is_file() or not os.access(tlapm, os.X_OK):
        errors.append(f"missing executable TLAPM: {tlapm}")

    version_output = ""
    output = ""
    returncode = None
    if not errors:
        version_run = subprocess.run(
            [str(tlapm), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        version_output = version_run.stdout.strip()
        if version_output != VER:
            errors.append(f"unexpected TLAPM version: {version_output!r}")

    if not errors:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        proof_run = subprocess.run(
            [
                str(tlapm),
                "-I",
                str(FORMAL),
                "-I",
                str(seed_formal),
                str(PROOF),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
        )
        output = proof_run.stdout
        returncode = proof_run.returncode
        print(output, end="" if output.endswith("\n") else "\n")
        if returncode:
            errors.append(f"TLAPM returned {returncode}")

    matches = re.findall(r"All ([0-9]+) obligations? proved\.", output)
    obligations = int(matches[-1]) if matches else None
    if not errors and obligations is None:
        errors.append("TLAPM success summary missing")
    if (
        not errors
        and evidence["status"] == "MECHANICALLY_PROVED"
        and (
            evidence["proof_gate"].get("verdict") != "MECHANICALLY_PROVED"
            or obligations != evidence["proof_gate"].get("obligations_proved")
        )
    ):
        errors.append("materialized Seed proof count/verdict mismatch")

    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-network-seed-tlaps-refinement-report",
        "schema_version": 1,
        "tlapm_commit": COMMIT,
        "tlapm_version": version_output,
        "seed_release_commit": SEED_COMMIT,
        "seed_resolution_sha256": "sha256:" + h(seed) if seed.is_file() else None,
        "bridge_sha256": "sha256:" + h(BRIDGE),
        "proof_sha256": "sha256:" + h(PROOF),
        "final_theorems": THEOREMS,
        "obligations_proved": obligations,
        "returncode": returncode,
        "errors": errors,
        "verdict": verdict,
    }
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"NETWORK_SEED_TLAPS_VERDICT={verdict}")
    for error in errors:
        print(f"NETWORK_SEED_TLAPS_ERROR={error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
