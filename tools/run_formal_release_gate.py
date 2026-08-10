#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "dist/formal-release-gate.json"
TLAPS_REPORT = ROOT / "dist/network-seed-refinement-proof.json"
CANON_TLAPS_REPORT = ROOT / "dist/network-canon-refinement-proof.json"


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
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    output = args.output.expanduser()
    if not output.is_absolute():
        output = ROOT / output

    tlapm = args.tlapm.expanduser().resolve()
    seed_root = args.seed_root.expanduser().resolve()
    python = sys.executable
    stages = [
        ("DIFF_CHECK", ["git", "diff", "--check"]),
        (
            "CANON_PROJECTION_CHECK",
            [python, "-m", "tools.generate_canon_tla_projection", "--check"],
        ),
        ("BUILD_CANON_PACKAGE", [python, "-m", "tools.build_canon_package"]),
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
    package = json.loads(
        (ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8")
    )
    relation = json.loads(
        (ROOT / "extension/canonical/formal/canon-tla-relation.json").read_text(
            encoding="utf-8"
        )
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
        "stages": results,
    }
    write_report(output, report)
    print(f"FORMAL_RELEASE_CANON_PACKAGE_DIGEST={package['package_digest']}")
    print(f"FORMAL_RELEASE_RELATION_DIGEST={relation['relation_digest']}")
    print(
        "FORMAL_RELEASE_CANON_REFINEMENT_STATUS="
        f"{relation['canon_projection']['status']}"
    )
    print(
        "FORMAL_RELEASE_CANON_REFINEMENT_OBLIGATIONS="
        f"{canon_tlaps_report['obligations_proved']}"
    )
    print(
        "FORMAL_RELEASE_SEED_REFINEMENT_OBLIGATIONS="
        f"{tlaps_report['obligations_proved']}"
    )
    print("FORMAL_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
