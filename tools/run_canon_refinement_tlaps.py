#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
MODEL = ROOT / "extension/canonical/source/network-extension-model.json"
REL = ROOT / "extension/canonical/assurance/canon-tla-refinement.json"
EVID = ROOT / "extension/canonical/assurance/canon-refinement-proof.json"
PROJ = FORMAL / "NetworkCanonProjection.tla"
TARGET = FORMAL / "NetworkExtension.tla"
PROOF = FORMAL / "NetworkCanonRefinementProofs.tla"
VER = "4600b24"
COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
PROFILE = "ASET-NETWORK-CANON-TLA-PROJECTION-V3"
THEOREMS = [
    "NetworkCanonCoreAlgebraEquivalent",
    "NetworkCoreSafetyPredicatesEquivalentToCanonProjection",
    "NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection",
]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def artifact_bindings() -> list[tuple[Path, str]]:
    return [
        (MODEL, "source_model"),
        (PROJ, "generated_projection"),
        (TARGET, "target_model"),
        (PROOF, "proof"),
    ]


def materialize_evidence(obligations: int) -> None:
    evidence = json.loads(EVID.read_text())
    for path, key in artifact_bindings():
        evidence["network_artifacts"][key]["sha256"] = sha(path)
    evidence["status"] = "MECHANICALLY_PROVED"
    gate = evidence["proof_gate"]
    gate["materialization"] = "REPRODUCED_WITH_PINNED_TLAPM"
    gate["obligations_proved"] = obligations
    gate["verdict"] = "MECHANICALLY_PROVED"

    relation = json.loads(REL.read_text())
    relation["source_model"]["sha256"] = sha(MODEL)
    relation["target_model"]["sha256"] = sha(TARGET)
    relation["proof_evidence"]["obligations_proved"] = obligations
    relation["proof_evidence"]["status"] = "MECHANICALLY_PROVED"
    relation["status"] = "MECHANICALLY_PROVED"

    write_json(EVID, evidence)
    write_json(REL, relation)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-canon-refinement-proof.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--materialize",
        action="store_true",
        help=(
            "After a successful proof with the pinned TLAPM, rewrite the exact "
            "canon proof evidence and refinement binding for the current artifacts."
        ),
    )
    args = parser.parse_args()

    tlapm = args.tlapm.expanduser().resolve()
    errors: list[str] = []
    relation = json.loads(REL.read_text())
    evidence = json.loads(EVID.read_text())
    gate = evidence["proof_gate"]

    if relation["generated_projection"]["profile"] != PROFILE:
        errors.append("projection profile mismatch")
    if evidence["projection_profile"] != PROFILE:
        errors.append("evidence projection profile mismatch")
    if gate["final_theorems"] != THEOREMS:
        errors.append("theorem set mismatch")
    if evidence["tlapm"] != {
        "required_commit": COMMIT,
        "required_version": VER,
    }:
        errors.append("pinned TLAPM identity mismatch")

    if not args.materialize:
        for path, key in artifact_bindings():
            if evidence["network_artifacts"][key]["sha256"] != sha(path):
                errors.append(f"{key} digest mismatch")
        if evidence["status"] != "MECHANICALLY_PROVED":
            errors.append("canon proof evidence requires rematerialization")
        if gate.get("verdict") != "MECHANICALLY_PROVED":
            errors.append("canon proof gate requires rematerialization")

    if not tlapm.is_file() or not os.access(tlapm, os.X_OK):
        errors.append(f"missing executable TLAPM: {tlapm}")

    projection_check = subprocess.run(
        [sys.executable, "-m", "tools.generate_canon_tla_projection", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(projection_check.stdout, end="")
    if projection_check.returncode:
        errors.append("generated projection stale")

    tlapm_version = ""
    if not errors:
        version_result = subprocess.run(
            [str(tlapm), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        tlapm_version = version_result.stdout.strip()
        if tlapm_version != VER:
            errors.append(f"unexpected TLAPM version: {tlapm_version!r}")

    proof_output = ""
    returncode = None
    if not errors:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        proof_result = subprocess.run(
            [str(tlapm), "-I", str(FORMAL), str(PROOF)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout_seconds,
        )
        proof_output = proof_result.stdout
        returncode = proof_result.returncode
        print(proof_output, end="" if proof_output.endswith("\n") else "\n")
        if returncode:
            errors.append(f"TLAPM returned {returncode}")

    matches = re.findall(r"All ([0-9]+) obligations? proved\.", proof_output)
    obligations = int(matches[-1]) if matches else None
    if not errors and obligations is None:
        errors.append("TLAPM success summary missing")
    if not errors and obligations != 3:
        errors.append(f"unexpected canon proof obligation count: {obligations}")

    if not errors and args.materialize:
        assert obligations is not None
        materialize_evidence(obligations)
        print("NETWORK_CANON_TLAPS_MATERIALIZATION=UPDATED")
    elif not errors and obligations != gate.get("obligations_proved"):
        errors.append("materialized canon proof count mismatch")

    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-network-canon-tlaps-refinement-report",
        "schema_version": 1,
        "profile": PROFILE,
        "tlapm_commit": COMMIT,
        "tlapm_version": tlapm_version,
        "source_model_sha256": sha(MODEL),
        "projection_sha256": sha(PROJ),
        "target_sha256": sha(TARGET),
        "proof_sha256": sha(PROOF),
        "final_theorems": THEOREMS,
        "obligations_proved": obligations,
        "returncode": returncode,
        "materialized": bool(args.materialize and not errors),
        "errors": errors,
        "verdict": verdict,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)

    print(f"NETWORK_CANON_TLAPS_VERDICT={verdict}")
    for error in errors:
        print(f"NETWORK_CANON_TLAPS_ERROR={error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
