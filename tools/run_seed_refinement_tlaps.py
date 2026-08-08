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
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"
PROOF_EVIDENCE = ROOT / "extension/canonical/assurance/seed-refinement-proof.json"

EXPECTED_TLAPM_VERSION = "4600b24"
EXPECTED_TLAPM_COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
EXPECTED_SEED_RELEASE_COMMIT = "633c130187b2a2bb42f24cfd66662d475de385d2"
EXPECTED_SEED_RESOLUTION_SHA256 = (
    "1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
)
FINAL_THEOREMS = (
    "NetworkSafetyRefinesSeedResolution",
    "NetworkEvaluatorMatchesSeedResolution",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    seed_root = args.seed_root.expanduser().resolve()
    seed_formal = seed_root / "seed/canonical/formal"
    seed_resolution = seed_formal / "SeedResolution.tla"
    output = args.output.expanduser()
    if not output.is_absolute():
        output = ROOT / output

    errors: list[str] = []
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    evidence = json.loads(PROOF_EVIDENCE.read_text(encoding="utf-8"))
    if binding["seed_release_commit"] != EXPECTED_SEED_RELEASE_COMMIT:
        errors.append("upstream binding is not the pinned Seed release commit")

    if not tlapm.is_file():
        errors.append(f"missing TLAPM executable: {tlapm}")
    elif not os.access(tlapm, os.X_OK):
        errors.append(f"TLAPM is not executable: {tlapm}")

    if not seed_resolution.is_file():
        errors.append(f"missing pinned SeedResolution.tla: {seed_resolution}")
    elif sha256(seed_resolution) != EXPECTED_SEED_RESOLUTION_SHA256:
        errors.append(
            "SeedResolution.tla digest mismatch: "
            f"expected {EXPECTED_SEED_RESOLUTION_SHA256}, got {sha256(seed_resolution)}"
        )

    for path in (BRIDGE, PROOF):
        if not path.is_file():
            errors.append(f"missing refinement artifact: {path}")

    if evidence.get("status") != "MECHANICALLY_PROVED":
        errors.append("Seed refinement proof evidence is not mechanically proved")
    gate = evidence.get("proof_gate", {})
    if gate.get("verdict") != "PASS":
        errors.append("Seed refinement proof evidence does not record PASS")
    if gate.get("final_theorems") != list(FINAL_THEOREMS):
        errors.append("Seed refinement proof evidence theorem set mismatch")
    if evidence.get("tlapm", {}).get("commit") != EXPECTED_TLAPM_COMMIT:
        errors.append("Seed refinement proof evidence TLAPM commit mismatch")
    if evidence.get("tlapm", {}).get("version") != EXPECTED_TLAPM_VERSION:
        errors.append("Seed refinement proof evidence TLAPM version mismatch")
    if evidence.get("upstream_seed", {}).get("release_commit") != EXPECTED_SEED_RELEASE_COMMIT:
        errors.append("Seed refinement proof evidence Seed release mismatch")
    if evidence.get("upstream_seed", {}).get("sha256") != (
        "sha256:" + EXPECTED_SEED_RESOLUTION_SHA256
    ):
        errors.append("Seed refinement proof evidence SeedResolution digest mismatch")
    artifacts = evidence.get("network_artifacts", {})
    for path, key in ((BRIDGE, "mapping"), (PROOF, "proof")):
        artifact = artifacts.get(key, {})
        if path.is_file() and artifact.get("sha256") != "sha256:" + sha256(path):
            errors.append(f"Seed refinement proof evidence {key} digest mismatch")

    proof_text = PROOF.read_text(encoding="utf-8") if PROOF.is_file() else ""
    for theorem in FINAL_THEOREMS:
        if re.search(rf"^THEOREM {re.escape(theorem)} ==\s*$", proof_text, re.MULTILINE) is None:
            errors.append(f"missing final theorem: {theorem}")

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

    print("NETWORK_SEED_TLAPS=START")
    print(f"TLAPM_COMMIT={EXPECTED_TLAPM_COMMIT}")
    print(f"TLAPM_VERSION={version_output}")
    print(f"SEED_RELEASE_COMMIT={EXPECTED_SEED_RELEASE_COMMIT}")
    print(f"SEED_RESOLUTION={seed_resolution}")
    if seed_resolution.is_file():
        print(f"SEED_RESOLUTION_SHA256=sha256:{sha256(seed_resolution)}")
    print(f"NETWORK_SEED_BRIDGE={BRIDGE.relative_to(ROOT)}")
    print(f"NETWORK_SEED_PROOF={PROOF.relative_to(ROOT)}")
    for theorem in FINAL_THEOREMS:
        print(f"NETWORK_SEED_FINAL_THEOREM={theorem}")

    output_text = ""
    returncode: int | None = None
    timed_out = False
    if not errors:
        shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
        cmd = [
            str(tlapm),
            "-I",
            str(FORMAL),
            "-I",
            str(seed_formal),
            str(PROOF),
        ]
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
            errors.append("TLAPS proof timed out")

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
            "TLAPM obligation count differs from recorded proof evidence: "
            f"expected {recorded_obligations}, got {obligations}"
        )
    for marker in forbidden:
        if marker in output_text:
            errors.append(f"TLAPM output contains {marker!r}")

    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-network-seed-tlaps-refinement-report",
        "schema_version": 1,
        "tlapm_commit": EXPECTED_TLAPM_COMMIT,
        "tlapm_version": version_output,
        "seed_release_commit": EXPECTED_SEED_RELEASE_COMMIT,
        "seed_resolution_path": str(seed_resolution),
        "seed_resolution_sha256": (
            "sha256:" + sha256(seed_resolution) if seed_resolution.is_file() else None
        ),
        "bridge": BRIDGE.relative_to(ROOT).as_posix(),
        "bridge_sha256": "sha256:" + sha256(BRIDGE) if BRIDGE.is_file() else None,
        "proof": PROOF.relative_to(ROOT).as_posix(),
        "proof_sha256": "sha256:" + sha256(PROOF) if PROOF.is_file() else None,
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
        print(f"NETWORK_SEED_TLAPS_OBLIGATIONS={obligations}")
    print(f"NETWORK_SEED_TLAPS_VERDICT={verdict}")
    for error in errors:
        print(f"NETWORK_SEED_TLAPS_ERROR={error}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
