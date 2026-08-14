from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.alpha4_network_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]
FINAL_THEOREM = "AssembledNetworkPreservesExactSeedObserveUnknownBoundary"
VERIFIER_MODULE = "AssembledNetworkReleaseProofs"


class NetworkReleaseTLAPSError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NetworkReleaseTLAPSError(message)


def default_tlapm() -> str:
    return os.environ.get("TLAPM_BIN", str(ROOT / ".tooling/tlapm/bin/tlapm"))


def parse_obligation_count(text: str) -> int | None:
    matches = re.findall(r"All\s+(\d+)\s+obligations?\s+proved\.", text)
    return int(matches[-1]) if matches else None


def verifier_source() -> str:
    return "\n".join(
        [
            "--------------- MODULE AssembledNetworkReleaseProofs ---------------",
            "EXTENDS AssembledNetwork, TLAPS",
            "",
            "Seed == INSTANCE ComponentRelations",
            "  WITH Subjects <- Sources,",
            "       Authorities <- Targets,",
            "       EvidenceItems <- EvidenceDigests,",
            "       AuthorityRecognition <- {}",
            "",
            "THEOREM AcceptedAdmissionMatchesExactSeedObserveUnknown ==",
            "  \\A ns, nt, observation, result, s, t :",
            "    /\\ Next(ns, nt, observation, result)",
            "    /\\ AcceptedResult(result)",
            "    /\\ Seed!ObserveUnknown(s, t, observation.evidence_digest)",
            "    => /\\ SeedProjectionRecognition(result) = t.recognition",
            "       /\\ SeedProjectionEffectPermitted(result) = FALSE",
            "       /\\ t.subject = s.subject",
            "       /\\ t.authority = s.authority",
            "       /\\ t.evidence = s.evidence \\cup {observation.evidence_digest}",
            "PROOF",
            "  BY DEF Next,",
            "         AdmitImport,",
            "         AdmitFresh,",
            "         AdmitReplay,",
            "         RejectConflict,",
            "         AcceptedResult,",
            "         SeedProjectionRecognition,",
            "         SeedProjectionEffectPermitted,",
            "         Seed!ObserveUnknown,",
            "         Seed!StateType",
            "",
            "THEOREM RejectedAdmissionClaimsNoSeedTransition ==",
            "  \\A ns, nt, observation, result :",
            "    /\\ Next(ns, nt, observation, result)",
            "    /\\ ~AcceptedResult(result)",
            '    => /\\ SeedProjectionRecognition(result) = "NOT_APPLICABLE"',
            "       /\\ SeedProjectionEffectPermitted(result) = FALSE",
            "PROOF",
            "  BY DEF Next,",
            "         AdmitImport,",
            "         AdmitFresh,",
            "         AdmitReplay,",
            "         RejectConflict,",
            "         AcceptedResult,",
            "         SeedProjectionRecognition,",
            "         SeedProjectionEffectPermitted",
            "",
            f"THEOREM {FINAL_THEOREM} ==",
            "  /\\ AcceptedAdmissionMatchesExactSeedObserveUnknown",
            "  /\\ RejectedAdmissionClaimsNoSeedTransition",
            "PROOF",
            "  BY AcceptedAdmissionMatchesExactSeedObserveUnknown,",
            "     RejectedAdmissionClaimsNoSeedTransition",
            "",
            "=====================================================================",
            "",
        ]
    )


def load_release_manifest(release_root: Path) -> dict[str, Any]:
    path = release_root / "RELEASE_MANIFEST.json"
    require(path.is_file(), "Network release manifest missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Network release manifest must be an object")
    require(
        value.get("document_type") == "aset-network-alpha4-release-materialization",
        "unexpected Network release manifest type",
    )
    assembled = value.get("assembled_formal")
    require(isinstance(assembled, dict), "Network assembled formal binding missing")
    require(assembled.get("scope") == "NETWORK_CORE_ADMISSION", "assembled formal scope drift")
    extension = value.get("extension_bindings")
    require(isinstance(extension, dict), "Network extension binding evidence missing")
    require(
        extension.get("relational") == "ObserveUnknown -> AdmitFresh,AdmitReplay",
        "Network relational Seed extension binding drift",
    )
    require(
        extension.get("rejected_branch") == "REJECT-CONFLICT -> NO_SEED_TRANSITION",
        "Network rejected-branch Seed boundary drift",
    )
    return value


def check_release_tlaps(release_root: Path, seed_release_root: Path, tlapm: str) -> dict[str, Any]:
    binding = parse_seed_binding()
    release_root = release_root.resolve()
    seed_release_root = seed_release_root.resolve()
    assembled = release_root / "formal/AssembledNetwork.tla"
    network_formal = release_root / "network/alpha4/formal"
    seed_formal = seed_release_root / "formal"
    require(assembled.is_file(), "materialized AssembledNetwork.tla missing")
    require(network_formal.is_dir(), "materialized Network formal source missing")
    require(seed_formal.is_dir(), "exact Seed release formal tree missing")
    require(
        tree_digest(seed_release_root) == binding.release_tree,
        "post-build proof Seed release tree mismatch",
    )
    component_relations = seed_formal / "ComponentRelations.tla"
    require(component_relations.is_file(), "exact Seed ComponentRelations.tla missing")
    require(
        sha256(component_relations) == binding.sources["seed/alpha4/formal/ComponentRelations.tla"],
        "post-build proof Seed relational bytes mismatch",
    )
    manifest = load_release_manifest(release_root)
    require(
        manifest["seed_base"]["tree_digest"] == binding.release_tree,
        "Network release was assembled against another Seed tree",
    )

    release_tree_before = tree_digest(release_root)
    seed_tree_before = tree_digest(seed_release_root)
    source = verifier_source()
    with tempfile.TemporaryDirectory(prefix="aset-network-release-tlaps-") as temp_dir:
        verification_root = Path(temp_dir)
        verifier = verification_root / f"{VERIFIER_MODULE}.tla"
        verifier.write_text(source, encoding="utf-8")
        command = [
            tlapm,
            "-I",
            str(release_root / "formal"),
            "-I",
            str(network_formal),
            "-I",
            str(seed_formal),
            str(verifier),
        ]
        try:
            result = subprocess.run(
                command,
                cwd=verification_root,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as error:
            raise NetworkReleaseTLAPSError(f"TLAPM invocation failed: {error}") from error

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    combined = result.stdout + "\n" + result.stderr
    obligations = parse_obligation_count(combined)
    require(result.returncode == 0, f"TLAPM returned {result.returncode}")
    require(obligations is not None and obligations > 0, "proved obligation count missing")
    require(
        tree_digest(release_root) == release_tree_before,
        "Network release tree changed during TLAPS verification",
    )
    require(
        tree_digest(seed_release_root) == seed_tree_before,
        "Seed release tree changed during Network TLAPS verification",
    )

    return {
        "document_type": "aset-network-release-assembled-tlaps-evidence",
        "schema_version": 1,
        "scope": "POST_BUILD_DEDUCTIVE_EXTENSION_ASSURANCE",
        "semantic_delta": "NONE",
        "semantic_precedence": "NONE",
        "semantic_source_runtime_dependency": "NONE",
        "release_binding": {
            "tree_digest": release_tree_before,
            "assembled_formal": {
                "path": "formal/AssembledNetwork.tla",
                "sha256": sha256(assembled),
            },
        },
        "seed_binding": {
            "release_tree_digest": seed_tree_before,
            "component_relations": {
                "path": "formal/ComponentRelations.tla",
                "sha256": sha256(component_relations),
            },
            "operator": "ObserveUnknown",
            "evidence_relation": "observation.evidence_digest",
            "authority_owner": "TARGET_LOCAL_SEED",
        },
        "proof": {
            "module": VERIFIER_MODULE,
            "module_materialization": "EPHEMERAL_VERIFIER_ONLY",
            "module_sha256": "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "final_theorem": FINAL_THEOREM,
            "obligations_proved": obligations,
        },
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--seed-release-root", type=Path, required=True)
    parser.add_argument("--tlapm", default=default_tlapm())
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-release-assembled-tlaps-evidence.json",
    )
    args = parser.parse_args()
    try:
        evidence = check_release_tlaps(args.release_root, args.seed_release_root, args.tlapm)
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        proof = evidence["proof"]
        print("ALPHA4_NETWORK_RELEASE_TLAPS_SCOPE=POST_BUILD_DEDUCTIVE_EXTENSION_ASSURANCE")
        print(f"ALPHA4_NETWORK_RELEASE_TLAPS_FINAL_THEOREM={proof['final_theorem']}")
        print(f"ALPHA4_NETWORK_RELEASE_TLAPS_OBLIGATIONS={proof['obligations_proved']} PASS")
        print(
            f"ALPHA4_NETWORK_RELEASE_TLAPS_TREE_DIGEST={evidence['release_binding']['tree_digest']}"
        )
        print(
            "ALPHA4_NETWORK_RELEASE_TLAPS_SEED_TREE_DIGEST="
            f"{evidence['seed_binding']['release_tree_digest']}"
        )
        print("ALPHA4_NETWORK_RELEASE_TLAPS_SEED_OPERATOR=ObserveUnknown")
        print("ALPHA4_NETWORK_RELEASE_TLAPS_SEMANTIC_DELTA=NONE")
        print("ALPHA4_NETWORK_RELEASE_TLAPS_SEMANTIC_SOURCE_DEPENDENCY=NONE")
        print("ALPHA4_NETWORK_RELEASE_TLAPS=PASS")
        return 0
    except (
        json.JSONDecodeError,
        OSError,
        ValueError,
        NetworkReleaseTLAPSError,
    ) as error:
        print(f"ALPHA4_NETWORK_RELEASE_TLAPS_ERROR={error}")
        print("ALPHA4_NETWORK_RELEASE_TLAPS=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
