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
RELATION = ROOT / "extension/canonical/assurance/canon-tla-refinement.json"
PROOF_EVIDENCE = ROOT / "extension/canonical/assurance/canon-refinement-proof.json"
PROJECTION = FORMAL / "NetworkCanonProjection.tla"
TARGET = FORMAL / "NetworkExtension.tla"
PROOF = FORMAL / "NetworkCanonRefinementProofs.tla"
GENERATOR = ROOT / "tools/generate_canon_tla_projection.py"

EXPECTED_TLAPM_VERSION = "4600b24"
EXPECTED_TLAPM_COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
EXPECTED_PROFILE = "ASET-NETWORK-CANON-TLA-PROJECTION-V2"
FINAL_THEOREMS = (
    "NetworkCanonCoreAlgebraEquivalent",
    "NetworkCoreSafetyPredicatesEquivalentToCanonProjection",
    "NetworkExtensionSafetyBehaviorallyEquivalentToCanonProjection",
)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-canon-refinement-proof.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    tlapm = args.tlapm.expanduser().resolve()
    output = args.output.expanduser()
    if not output.is_absolute():
        output = ROOT / output

    errors: list[str] = []
    relation = json.loads(RELATION.read_text(encoding="utf-8"))
    evidence = json.loads(PROOF_EVIDENCE.read_text(encoding="utf-8"))
    generated = relation.get("generated_projection", {})
    source = relation.get("source_model", {})
    target = relation.get("target_model", {})
    proof_binding = relation.get("proof", {})

    if generated.get("profile") != EXPECTED_PROFILE:
        errors.append("canon projection profile mismatch")
    if source.get("sha256") != sha256(MODEL):
        errors.append("canon refinement source-model digest mismatch")
    if target.get("sha256") != sha256(TARGET):
        errors.append("canon refinement target-model digest mismatch")
    if generated.get("path") != PROJECTION.relative_to(ROOT).as_posix():
        errors.append("canon projection path mismatch")
    if proof_binding.get("module") != PROOF.relative_to(ROOT).as_posix():
        errors.append("canon refinement proof path mismatch")
    if proof_binding.get("final_theorem") != FINAL_THEOREMS[-1]:
        errors.append("canon refinement final theorem mismatch")

    if relation.get("status") != "MECHANICALLY_PROVED":
        errors.append("canon refinement relation is not mechanically proved")
    if evidence.get("status") != "MECHANICALLY_PROVED":
        errors.append("canon refinement proof evidence is not mechanically proved")
    if evidence.get("projection_profile") != EXPECTED_PROFILE:
        errors.append("canon refinement proof evidence projection profile mismatch")
    gate = evidence.get("proof_gate", {})
    if gate.get("verdict") != "PASS":
        errors.append("canon refinement proof evidence does not record PASS")
    if gate.get("final_theorems") != list(FINAL_THEOREMS):
        errors.append("canon refinement proof evidence theorem set mismatch")
    if gate.get("obligation_count_semantics") != "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT":
        errors.append("canon refinement proof evidence obligation-count semantics mismatch")
    if evidence.get("tlapm", {}).get("commit") != EXPECTED_TLAPM_COMMIT:
        errors.append("canon refinement proof evidence TLAPM commit mismatch")
    if evidence.get("tlapm", {}).get("version") != EXPECTED_TLAPM_VERSION:
        errors.append("canon refinement proof evidence TLAPM version mismatch")
    artifacts = evidence.get("network_artifacts", {})
    for path, key in (
        (MODEL, "source_model"),
        (PROJECTION, "generated_projection"),
        (TARGET, "target_model"),
        (PROOF, "proof"),
    ):
        artifact = artifacts.get(key, {})
        if path.is_file() and artifact.get("sha256") != sha256(path):
            errors.append(f"canon refinement proof evidence {key} digest mismatch")

    for path in (MODEL, RELATION, PROOF_EVIDENCE, PROJECTION, TARGET, PROOF, GENERATOR):
        if not path.is_file():
            errors.append(f"missing canon refinement artifact: {path}")

    projection_text = PROJECTION.read_text(encoding="utf-8") if PROJECTION.is_file() else ""
    if "GENERATED FILE. DO NOT EDIT." not in projection_text:
        errors.append("generated projection marker missing")
    if (
        "EXTENDS NetworkExtension" in projection_text
        or "INSTANCE NetworkExtension" in projection_text
    ):
        errors.append("generated projection depends on handwritten target model")

    proof_text = PROOF.read_text(encoding="utf-8") if PROOF.is_file() else ""
    for theorem in FINAL_THEOREMS:
        if re.search(rf"^THEOREM {re.escape(theorem)} ==\s*$", proof_text, re.MULTILINE) is None:
            errors.append(f"missing canon refinement theorem: {theorem}")
    if "Canon == INSTANCE NetworkCanonProjection" not in proof_text:
        errors.append("canon refinement proof does not instantiate generated projection")

    if not tlapm.is_file():
        errors.append(f"missing TLAPM executable: {tlapm}")
    elif not os.access(tlapm, os.X_OK):
        errors.append(f"TLAPM is not executable: {tlapm}")

    version_output = ""
    if tlapm.is_file() and os.access(tlapm, os.X_OK):
        result = subprocess.run(
            [str(tlapm), "--version"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        version_output = result.stdout.strip()
        if result.returncode != 0:
            errors.append(f"tlapm --version returned {result.returncode}")
        if version_output != EXPECTED_TLAPM_VERSION:
            errors.append(f"unexpected TLAPM version: {version_output!r}")

    projection_check = subprocess.run(
        [sys.executable, os.fspath(GENERATOR), "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if projection_check.returncode != 0:
        errors.append("committed generated Network canon projection is stale")

    print("NETWORK_CANON_TLAPS=START")
    print(f"TLAPM_COMMIT={EXPECTED_TLAPM_COMMIT}")
    print(f"TLAPM_VERSION={version_output}")
    print(f"NETWORK_CANON_PROFILE={EXPECTED_PROFILE}")
    print(f"NETWORK_CANON_SOURCE_SHA256={sha256(MODEL)}")
    print(f"NETWORK_CANON_PROJECTION={PROJECTION.relative_to(ROOT)}")
    print(f"NETWORK_CANON_PROJECTION_SHA256={sha256(PROJECTION)}")
    print(f"NETWORK_CANON_TARGET={TARGET.relative_to(ROOT)}")
    print(f"NETWORK_CANON_TARGET_SHA256={sha256(TARGET)}")
    print(f"NETWORK_CANON_PROOF={PROOF.relative_to(ROOT)}")
    for theorem in FINAL_THEOREMS:
        print(f"NETWORK_CANON_FINAL_THEOREM={theorem}")

    if projection_check.stdout:
        print(projection_check.stdout, end="" if projection_check.stdout.endswith("\n") else "\n")

    output_text = ""
    returncode: int | None = None
    timed_out = False
    if not errors:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        cmd = [str(tlapm), "-I", str(FORMAL), str(PROOF)]
        try:
            result = subprocess.run(
                cmd,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=args.timeout_seconds,
                check=False,
            )
            output_text = result.stdout
            returncode = result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            output_text = captured
            errors.append("TLAPS canon refinement proof timed out")

    if output_text:
        print(output_text, end="" if output_text.endswith("\n") else "\n")

    matches = re.findall(r"All ([0-9]+) obligations? proved\.", output_text)
    obligations = int(matches[-1]) if matches else None
    forbidden = (
        "obligations failed",
        "unproved obligations",
        "backend errors",
        "Zenon error",
        "Proof.Parser",
        "[ERROR]",
    )
    if returncode != 0:
        errors.append(f"TLAPM returned {returncode}")
    if obligations is None:
        errors.append("TLAPM success summary was not found")
    recorded_obligations = gate.get("obligations_proved")
    if obligations is not None and obligations != recorded_obligations:
        errors.append(
            "TLAPM obligation count differs from recorded canon proof evidence: "
            f"expected {recorded_obligations}, got {obligations}"
        )
    for marker in forbidden:
        if marker in output_text:
            errors.append(f"TLAPM output contains {marker!r}")

    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-network-canon-tlaps-refinement-report",
        "schema_version": 1,
        "profile": EXPECTED_PROFILE,
        "tlapm_commit": EXPECTED_TLAPM_COMMIT,
        "tlapm_version": version_output,
        "source_model": MODEL.relative_to(ROOT).as_posix(),
        "source_model_sha256": sha256(MODEL),
        "projection": PROJECTION.relative_to(ROOT).as_posix(),
        "projection_sha256": sha256(PROJECTION) if PROJECTION.is_file() else None,
        "target": TARGET.relative_to(ROOT).as_posix(),
        "target_sha256": sha256(TARGET) if TARGET.is_file() else None,
        "proof": PROOF.relative_to(ROOT).as_posix(),
        "proof_sha256": sha256(PROOF) if PROOF.is_file() else None,
        "final_theorems": list(FINAL_THEOREMS),
        "proof_evidence": PROOF_EVIDENCE.relative_to(ROOT).as_posix(),
        "recorded_obligations": gate.get("obligations_proved"),
        "obligations_proved": obligations,
        "returncode": returncode,
        "timed_out": timed_out,
        "errors": errors,
        "verdict": verdict,
    }
    write_report(output, report)
    if obligations is not None:
        print(f"NETWORK_CANON_TLAPS_OBLIGATIONS={obligations}")
    print(f"NETWORK_CANON_TLAPS_VERDICT={verdict}")
    for error in errors:
        print(f"NETWORK_CANON_TLAPS_ERROR={error}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
