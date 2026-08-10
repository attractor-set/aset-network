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
GEN = ROOT / "tools/generate_canon_tla_projection.py"
VER = "4600b24"
COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
PROFILE = "ASET-NETWORK-CANON-TLA-PROJECTION-V3"
THEOREMS = [
    "NetworkCanonCoreAlgebraEquivalent",
    "NetworkCoreSafetyPredicatesEquivalentToCanonProjection",
    "NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection",
]


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tlapm", type=Path, required=True)
    ap.add_argument(
        "--output", type=Path, default=ROOT / "dist/network-canon-refinement-proof.json"
    )
    ap.add_argument("--timeout-seconds", type=int, default=900)
    a = ap.parse_args()
    tl = a.tlapm.expanduser().resolve()
    errs = []
    r = json.loads(REL.read_text())
    e = json.loads(EVID.read_text())
    gate = e["proof_gate"]
    if r["generated_projection"]["profile"] != PROFILE or e["projection_profile"] != PROFILE:
        errs.append("projection profile mismatch")
    for p, key in [
        (MODEL, "source_model"),
        (PROJ, "generated_projection"),
        (TARGET, "target_model"),
        (PROOF, "proof"),
    ]:
        if e["network_artifacts"][key]["sha256"] != sha(p):
            errs.append(f"{key} digest mismatch")
    if gate["final_theorems"] != THEOREMS:
        errs.append("theorem set mismatch")
    if not tl.is_file() or not os.access(tl, os.X_OK):
        errs.append(f"missing executable TLAPM: {tl}")
    chk = subprocess.run(
        [sys.executable, "-m", "tools.generate_canon_tla_projection", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(chk.stdout, end="")
    if chk.returncode:
        errs.append("generated projection stale")
    vo = ""
    if not errs:
        vr = subprocess.run(
            [str(tl), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        vo = vr.stdout.strip()
        if vo != VER:
            errs.append(f"unexpected TLAPM version: {vo!r}")
    out = ""
    rc = None
    if not errs:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        rr = subprocess.run(
            [str(tl), "-I", str(FORMAL), str(PROOF)],
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
            gate.get("verdict") != "MECHANICALLY_PROVED"
            or obligations != gate.get("obligations_proved")
        )
    ):
        errs.append("materialized canon proof count/verdict mismatch")
    verdict = "PASS" if not errs else "FAIL"
    report = {
        "document_type": "aset-network-canon-tlaps-refinement-report",
        "schema_version": 1,
        "profile": PROFILE,
        "tlapm_commit": COMMIT,
        "tlapm_version": vo,
        "source_model_sha256": sha(MODEL),
        "projection_sha256": sha(PROJ),
        "target_sha256": sha(TARGET),
        "proof_sha256": sha(PROOF),
        "final_theorems": THEOREMS,
        "obligations_proved": obligations,
        "returncode": rc,
        "errors": errs,
        "verdict": verdict,
    }
    outp = a.output if a.output.is_absolute() else ROOT / a.output
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"NETWORK_CANON_TLAPS_VERDICT={verdict}")
    for x in errs:
        print(f"NETWORK_CANON_TLAPS_ERROR={x}")
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
