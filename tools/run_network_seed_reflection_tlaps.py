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
PROFILE = ROOT / "theory/network-seed-reflection/EXPRESSION_ASSURANCE.json"
TLAPM_VERSION = "4600b24"
TLAPM_COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-seed-reflection-proof.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    oracle = profile["formal_oracle"]
    seed_subject = oracle["seed_subject"]
    tlapm = args.tlapm.expanduser().resolve()
    seed_root = args.seed_root.expanduser().resolve()
    seed_formal = seed_root / "seed/canonical/formal"
    seed = seed_root / seed_subject["seed_resolution_path"]
    formal = ROOT / "theory/network-seed-reflection/formal"
    proof = ROOT / oracle["proof"]["path"]
    errors: list[str] = []

    for artifact_name in ("network_model", "mapping", "proof"):
        artifact = oracle[artifact_name]
        path = ROOT / artifact["path"]
        if not path.is_file() or digest(path) != artifact["sha256"]:
            errors.append(f"retained {artifact_name} digest mismatch")

    if not seed.is_file() or digest(seed) != seed_subject["seed_resolution_sha256"]:
        errors.append("SeedResolution.tla digest mismatch")
    if (seed_root / ".git").exists():
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=seed_root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            commit = ""
        if commit != seed_subject["release_commit"]:
            errors.append("pinned Seed release commit mismatch")

    if not tlapm.is_file() or not os.access(tlapm, os.X_OK):
        errors.append(f"missing executable TLAPM: {tlapm}")

    version_output = ""
    proof_output = ""
    returncode: int | None = None
    if not errors:
        version_run = subprocess.run(
            [str(tlapm), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        version_output = version_run.stdout.strip()
        if version_output != TLAPM_VERSION:
            errors.append(f"unexpected TLAPM version: {version_output!r}")

    if not errors:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        proof_run = subprocess.run(
            [str(tlapm), "-I", str(formal), "-I", str(seed_formal), str(proof)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
            check=False,
        )
        proof_output = proof_run.stdout
        returncode = proof_run.returncode
        print(proof_output, end="" if proof_output.endswith("\n") else "\n")
        if returncode:
            errors.append(f"TLAPM returned {returncode}")

    matches = re.findall(r"All ([0-9]+) obligations? proved\.", proof_output)
    obligations = int(matches[-1]) if matches else None
    if not errors and obligations != oracle["obligations_proved"]:
        expected = oracle["obligations_proved"]
        errors.append(f"proof obligation count mismatch: expected {expected}, got {obligations}")

    proof_text = proof.read_text(encoding="utf-8")
    for theorem in oracle["final_theorems"]:
        if f"THEOREM {theorem} ==" not in proof_text:
            errors.append(f"final theorem missing: {theorem}")

    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-network-retained-seed-reflection-tlaps-report",
        "schema_version": 1,
        "assurance_id": profile["assurance_id"],
        "historical_network_subject": profile["historical_subject"],
        "tlapm_commit": TLAPM_COMMIT,
        "tlapm_version": version_output,
        "seed_release_commit": seed_subject["release_commit"],
        "seed_resolution_sha256": digest(seed) if seed.is_file() else None,
        "final_theorems": oracle["final_theorems"],
        "obligations_proved": obligations,
        "returncode": returncode,
        "errors": errors,
        "verdict": verdict,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"NETWORK_SEED_REFLECTION_TLAPS_OBLIGATIONS={obligations or 0}")
    print(f"NETWORK_SEED_REFLECTION_TLAPS={verdict}")
    for error in errors:
        print(f"NETWORK_SEED_REFLECTION_TLAPS_ERROR={error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
