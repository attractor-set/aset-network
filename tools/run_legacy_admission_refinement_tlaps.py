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
F = ROOT / "extension/canonical/formal"
M = F / "NetworkLegacyAdmissionRefinement.tla"
P = F / "NetworkLegacyAdmissionRefinementProofs.tla"
E = ROOT / "extension/canonical/assurance/legacy-admission-refinement-proof.json"
VER = "4600b24"
COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tlapm", type=Path, required=True)
    ap.add_argument(
        "--output", type=Path, default=ROOT / "dist/network-legacy-admission-refinement-proof.json"
    )
    ap.add_argument("--timeout-seconds", type=int, default=900)
    a = ap.parse_args()
    tl = a.tlapm.expanduser().resolve()
    e = json.loads(E.read_text())
    errs = []
    for p, key in [(M, "mapping"), (P, "proof")]:
        if e["artifacts"][key]["sha256"] != sha(p):
            errs.append(f"{key} digest mismatch")
    if not tl.is_file() or not os.access(tl, os.X_OK):
        errs.append(f"missing executable TLAPM: {tl}")
    vo = ""
    out = ""
    rc = None
    if not errs:
        vr = subprocess.run(
            [str(tl), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        vo = vr.stdout.strip()
        if vo != VER:
            errs.append(f"unexpected TLAPM version: {vo!r}")
    if not errs:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        rr = subprocess.run(
            [str(tl), "-I", str(F), str(P)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=a.timeout_seconds,
        )
        out = rr.stdout
        rc = rr.returncode
        print(out, end="" if out.endswith("\n") else "\n")
        if rc:
            errs.append(f"TLAPM returned {rc}")
    m = re.findall(r"All ([0-9]+) obligations? proved\.", out)
    obligations = int(m[-1]) if m else None
    if not errs and obligations is None:
        errs.append("TLAPM success summary missing")
    if (
        not errs
        and e["status"] == "MECHANICALLY_PROVED"
        and (
            e["proof_gate"].get("verdict") != "MECHANICALLY_PROVED"
            or obligations != e["proof_gate"].get("obligations_proved")
        )
    ):
        errs.append("materialized legacy proof count/verdict mismatch")
    verdict = "PASS" if not errs else "FAIL"
    report = {
        "document_type": "aset-network-legacy-admission-tlaps-report",
        "schema_version": 1,
        "tlapm_commit": COMMIT,
        "tlapm_version": vo,
        "mapping_sha256": sha(M),
        "proof_sha256": sha(P),
        "final_theorem": "LegacyNetworkRefinesMinimalAdmission",
        "obligations_proved": obligations,
        "returncode": rc,
        "errors": errs,
        "verdict": verdict,
    }
    op = a.output if a.output.is_absolute() else ROOT / a.output
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"NETWORK_LEGACY_ADMISSION_TLAPS_VERDICT={verdict}")
    for x in errs:
        print(f"NETWORK_LEGACY_ADMISSION_TLAPS_ERROR={x}")
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
