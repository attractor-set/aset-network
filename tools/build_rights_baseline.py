#!/usr/bin/env python3
"""Build a non-normative machine-readable rights/provenance baseline.

This tool does not create, transfer, or register legal rights.  It records exact
repository and artifact identities for a frozen release so the same identities
can be used in a registration/deposit package or internal rights record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS = (
    "LICENSE",
    "pyproject.toml",
    "extension/canonical/CANON_PACKAGE.json",
    "extension/canonical/source/network-extension-model.json",
    "extension/canonical/formal/canon-tla-relation.json",
    "extension/canonical/formal/NetworkCanonProjection.tla",
    "extension/canonical/formal/NetworkExtension.tla",
    "extension/canonical/formal/NetworkCanonRefinementProofs.tla",
    "extension/canonical/formal/NetworkExtensionSeedRefinement.tla",
    "extension/canonical/formal/NetworkExtensionSeedRefinementProofs.tla",
    "extension/canonical/profiles/federation/assurance/FederationProfile.tla",
    "extension/canonical/assurance/profile-compositions/federation-liveness/FederationCompositionLiveness.tla",
    "extension/canonical/assurance/canon-refinement-proof.json",
    "extension/canonical/assurance/seed-refinement-proof.json",
    "upstream/ASET_SEED_BINDING.json",
)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def read_json_if_present(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def exact_artifacts() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative in ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            continue
        item: dict[str, Any] = {
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        parsed = read_json_if_present(path)
        if parsed is not None:
            item["json"] = parsed
        result[relative] = item
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True, help="Release identifier/tag")
    parser.add_argument(
        "--work-title",
        default="ASET Network Extension",
        help="Human-readable work title",
    )
    parser.add_argument(
        "--output",
        default="dist/network-extension-rights-baseline.json",
        help="Output path relative to repository root",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow tracked modifications in the working tree",
    )
    args = parser.parse_args()

    tracked_status = run_git("status", "--porcelain", "--untracked-files=no")
    if tracked_status and not args.allow_dirty:
        print("RIGHTS_BASELINE=FAIL")
        print("RIGHTS_BASELINE_ERROR=tracked working tree is not clean")
        return 2

    commit = run_git("rev-parse", "HEAD")
    tree = run_git("rev-parse", "HEAD^{tree}")
    branch = run_git("branch", "--show-current")
    remote = ""
    try:
        remote = run_git("remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        pass

    tag_target = ""
    tag_matches_head = False
    try:
        tag_target = run_git("rev-list", "-n", "1", args.release)
        tag_matches_head = tag_target == commit
    except subprocess.CalledProcessError:
        pass

    baseline = {
        "schema": "ASET-NETWORK-RIGHTS-BASELINE-V1",
        "status": "NON_NORMATIVE_PROVENANCE_EVIDENCE",
        "legal_effect": "NONE_BY_ITSELF",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "work": {
            "title": args.work_title,
            "release": args.release,
            "repository": remote,
        },
        "git": {
            "commit": commit,
            "tree": tree,
            "branch": branch,
            "tracked_worktree_clean": not bool(tracked_status),
            "release_tag_target": tag_target or None,
            "release_tag_matches_head": tag_matches_head,
        },
        "artifacts": exact_artifacts(),
        "notes": [
            "This file records exact identities; it does not create or transfer rights.",
            "Formal proof obligation counts are release evidence, not normative semantics.",
            "Personal filing data and executed private agreements must not be embedded here.",
        ],
    }

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"RIGHTS_BASELINE={output.relative_to(ROOT)}")
    print(f"RIGHTS_BASELINE_SHA256={sha256_file(output)}")
    print(f"RIGHTS_BASELINE_COMMIT={commit}")
    print(f"RIGHTS_BASELINE_TREE={tree}")
    print(f"RIGHTS_BASELINE_TAG_MATCH={str(tag_matches_head).lower()}")
    print("RIGHTS_BASELINE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
