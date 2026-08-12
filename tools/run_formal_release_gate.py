#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "dist/formal-release-gate.json"
TLAPS_REPORT = ROOT / "dist/network-seed-refinement-proof.json"
CANON_TLAPS_REPORT = ROOT / "dist/network-canon-refinement-proof.json"
SEED_PROJECTION_ASSURANCE_REPORT = ROOT / "dist/network-seed-projection-assurance.json"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_stage(name: str, command: list[str]) -> dict[str, object]:
    print(f"FORMAL_RELEASE_STAGE={name}:START")
    result = subprocess.run(command, cwd=ROOT, check=False)
    verdict = "PASS" if result.returncode == 0 else "FAIL"
    print(f"FORMAL_RELEASE_STAGE={name}:{verdict}")
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument("--seed-root", type=Path, default=Path.home() / "ASET")
    parser.add_argument("--assurance-root", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    output = args.output.expanduser()
    if not output.is_absolute():
        output = ROOT / output

    tlapm = args.tlapm.expanduser().resolve()
    seed_root = args.seed_root.expanduser().resolve()
    assurance_root = args.assurance_root.expanduser().resolve()
    python = sys.executable
    stages = [
        ("DIFF_CHECK", ["git", "diff", "--check"]),
        ("TRACKED_WORKTREE_CLEAN", ["git", "diff", "--quiet", "HEAD", "--"]),
        (
            "TRACKED_INDEX_CLEAN",
            ["git", "diff", "--cached", "--quiet", "HEAD", "--"],
        ),
        ("PYTHON_FORMAT", ["ruff", "format", "--check", "."]),
        ("PYTHON_LINT", ["ruff", "check", "."]),
        (
            "CANON_PROJECTION_CHECK",
            [python, "-m", "tools.generate_canon_tla_projection", "--check"],
        ),
        (
            "FORMAL_RELATION_CHECK",
            [python, "-m", "tools.build_formal_relation", "--check"],
        ),
        (
            "CANON_PACKAGE_CHECK",
            [python, "-m", "tools.build_canon_package", "--check"],
        ),
        ("VALIDATE", [python, "-m", "tools.validate_extension"]),
        ("CONFORMANCE", [python, "-m", "tools.run_conformance"]),
        ("TESTS", [python, "-m", "pytest", "-q"]),
        ("TLC", [python, "-m", "tools.run_tlc", "all"]),
        (
            "TLAPS_CANON_REFINEMENT",
            [
                python,
                "-m",
                "tools.run_canon_refinement_tlaps",
                "--tlapm",
                str(tlapm),
                "--timeout-seconds",
                str(args.timeout_seconds),
            ],
        ),
        (
            "TLAPS_SEED_REFINEMENT",
            [
                python,
                "-m",
                "tools.run_seed_refinement_tlaps",
                "--tlapm",
                str(tlapm),
                "--seed-root",
                str(seed_root),
                "--timeout-seconds",
                str(args.timeout_seconds),
            ],
        ),
        (
            "SEED_PROJECTION_ASSURANCE",
            [
                python,
                "-m",
                "tools.check_seed_projection_assurance",
                "--seed-root",
                str(assurance_root),
                "--output",
                str(SEED_PROJECTION_ASSURANCE_REPORT),
            ],
        ),
        (
            "TRACKED_WORKTREE_UNCHANGED",
            ["git", "diff", "--quiet", "HEAD", "--"],
        ),
        (
            "TRACKED_INDEX_UNCHANGED",
            ["git", "diff", "--cached", "--quiet", "HEAD", "--"],
        ),
    ]

    results = []
    for name, command in stages:
        result = run_stage(name, command)
        results.append(result)
        if result["verdict"] != "PASS":
            write_report(
                output,
                {
                    "document_type": "aset-network-formal-release-gate-report",
                    "schema_version": 1,
                    "verdict": "FAIL",
                    "failed_stage": name,
                    "stages": results,
                },
            )
            print("FORMAL_RELEASE_GATE=FAIL")
            print(f"FORMAL_RELEASE_GATE_FAILED_STAGE={name}")
            return 1

    canon_tlaps_report = json.loads(CANON_TLAPS_REPORT.read_text(encoding="utf-8"))
    tlaps_report = json.loads(TLAPS_REPORT.read_text(encoding="utf-8"))
    projection_assurance_report = json.loads(
        SEED_PROJECTION_ASSURANCE_REPORT.read_text(encoding="utf-8")
    )
    composition_errors: list[str] = []
    if projection_assurance_report.get("verdict") != "PASS":
        composition_errors.append("projection assurance verdict is not PASS")
    if projection_assurance_report.get("network_seed_refinement_obligations") != tlaps_report.get(
        "obligations_proved"
    ):
        composition_errors.append("projection assurance and fresh Seed TLAPS count differ")
    if projection_assurance_report.get("shared_seed_resolution_sha256") != tlaps_report.get(
        "seed_resolution_sha256"
    ):
        composition_errors.append("projection assurance and fresh Seed TLAPS subject differ")
    if composition_errors:
        write_report(
            output,
            {
                "document_type": "aset-network-formal-release-gate-report",
                "schema_version": 1,
                "verdict": "FAIL",
                "failed_stage": "EVIDENCE_COMPOSITION_CHECK",
                "errors": composition_errors,
                "stages": results,
            },
        )
        print("FORMAL_RELEASE_GATE=FAIL")
        print("FORMAL_RELEASE_GATE_FAILED_STAGE=EVIDENCE_COMPOSITION_CHECK")
        for error in composition_errors:
            print(f"FORMAL_RELEASE_GATE_ERROR={error}")
        return 1

    package = json.loads(
        (ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8")
    )
    relation = json.loads(
        (ROOT / "extension/canonical/formal/canon-tla-relation.json").read_text(encoding="utf-8")
    )
    report = {
        "document_type": "aset-network-formal-release-gate-report",
        "schema_version": 1,
        "verdict": "PASS",
        "canon_package_digest": package["package_digest"],
        "formal_relation_digest": relation["relation_digest"],
        "canon_projection_profile": relation["canon_projection"]["profile"],
        "canon_refinement_status": relation["canon_projection"]["status"],
        "canon_refinement_obligations_proved": canon_tlaps_report["obligations_proved"],
        "seed_refinement_status": relation["seed_refinement"]["status"],
        "seed_refinement_obligations_proved": tlaps_report["obligations_proved"],
        "tlapm_commit": tlaps_report["tlapm_commit"],
        "seed_release_commit": tlaps_report["seed_release_commit"],
        "seed_resolution_sha256": tlaps_report["seed_resolution_sha256"],
        "seed_projection_assurance_id": projection_assurance_report["assurance_id"],
        "seed_projection_assurance_verdict": projection_assurance_report["verdict"],
        "seed_projection_assurance_report_sha256": sha256_file(SEED_PROJECTION_ASSURANCE_REPORT),
        "public_v60_assurance_id": projection_assurance_report["public_v60_assurance_id"],
        "public_v60_package_digest": projection_assurance_report["public_v60_package_digest"],
        "public_v60_expected_tlaps_obligations": projection_assurance_report[
            "public_v60_expected_tlaps_obligations"
        ],
        "seed_projection_composition_type": projection_assurance_report["composition_type"],
        "stages": results,
    }
    write_report(output, report)
    print(f"FORMAL_RELEASE_CANON_PACKAGE_DIGEST={package['package_digest']}")
    print(f"FORMAL_RELEASE_RELATION_DIGEST={relation['relation_digest']}")
    print(f"FORMAL_RELEASE_CANON_REFINEMENT_STATUS={relation['canon_projection']['status']}")
    print(f"FORMAL_RELEASE_CANON_REFINEMENT_OBLIGATIONS={canon_tlaps_report['obligations_proved']}")
    print(f"FORMAL_RELEASE_SEED_REFINEMENT_OBLIGATIONS={tlaps_report['obligations_proved']}")
    print(f"FORMAL_RELEASE_SEED_PROJECTION_ASSURANCE={projection_assurance_report['verdict']}")
    print("FORMAL_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
