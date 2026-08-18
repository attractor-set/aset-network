from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from tools.alpha4_network_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]
FINAL_THEOREM = "AssembledNetworkPreservesExactSeedObserveUnknownBoundary"


class NetworkReleaseAdmissionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NetworkReleaseAdmissionError(message)


def load_json(path: Path, label: str) -> dict[str, Any]:
    require(path.is_file(), f"{label} missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def archive_tree_digest(archive_path: Path, archive_root_name: str) -> tuple[str, set[str]]:
    require(archive_path.is_file(), f"archive missing: {archive_path}")
    prefix = archive_root_name.rstrip("/") + "/"
    digest = hashlib.sha256()
    paths: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        for info in sorted(entries, key=lambda item: item.filename):
            require(info.filename.startswith(prefix), "archive root mismatch")
            relative = info.filename[len(prefix) :]
            require(relative and not relative.startswith("/"), "invalid archive path")
            require(".." not in Path(relative).parts, "unsafe archive path")
            require(relative not in paths, "duplicate archive path")
            paths.add(relative)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(archive.read(info))
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest(), paths


def tree_paths(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def check_admission(
    release_root: Path,
    profiles_root: Path,
    proof_evidence_path: Path,
    airgap_evidence_path: Path,
    release_archive: Path,
    profiles_archive: Path,
) -> dict[str, Any]:
    binding = parse_seed_binding()
    release_root = release_root.resolve()
    profiles_root = profiles_root.resolve()
    release_manifest = load_json(release_root / "RELEASE_MANIFEST.json", "Network release manifest")
    profiles_manifest = load_json(
        profiles_root / "RELEASE_PROFILE_MANIFEST.json", "Network profile manifest"
    )
    companion_evidence_path = profiles_manifest.get("companion_extension_evidence")
    require(
        isinstance(companion_evidence_path, str) and companion_evidence_path,
        "Network companion extension evidence binding missing",
    )
    companion_evidence = load_json(
        profiles_root / companion_evidence_path, "Network companion extension evidence"
    )
    proof = load_json(proof_evidence_path, "post-build TLAPS evidence")
    airgap = load_json(airgap_evidence_path, "Python air-gap evidence")

    require(
        release_manifest.get("document_type") == "aset-network-alpha4-release-materialization",
        "release manifest type mismatch",
    )
    require(
        profiles_manifest.get("document_type")
        == "aset-network-alpha4-release-companion-materialization",
        "profile manifest type mismatch",
    )
    require(
        release_manifest.get("semantic_precedence") == "NONE",
        "Network release acquired semantic precedence",
    )
    require(
        profiles_manifest.get("semantic_precedence") == "NONE",
        "Network companions acquired semantic precedence",
    )
    require(
        companion_evidence.get("status") == "PASS"
        and companion_evidence.get("semantic_precedence") == "NONE"
        and companion_evidence.get("relation") == "EXTENSION_OF_EXACT_SEED_COMPANIONS",
        "Network companion extension evidence not admitted",
    )
    require(
        companion_evidence.get("english_components_checked") == 21,
        "Network English companion coverage mismatch",
    )
    require(
        release_manifest.get("assurance_representations")
        == ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "Network assurance representation surface drift",
    )

    release_tree = tree_digest(release_root)
    profiles_tree = tree_digest(profiles_root)
    require(
        profiles_manifest.get("network_release_tree_digest") == release_tree,
        "Network companions are not bound to exact Network release tree",
    )
    require(
        release_manifest.get("seed_base", {}).get("tree_digest") == binding.release_tree,
        "Network release Seed base drift",
    )
    require(
        profiles_manifest.get("seed_release_tree_digest") == binding.release_tree,
        "Network profile Seed release binding drift",
    )
    require(
        profiles_manifest.get("seed_profile_tree_digest") == binding.profile_tree,
        "Network profile Seed companion binding drift",
    )

    proof_binding = proof.get("release_binding")
    seed_binding = proof.get("seed_binding")
    proof_subject = proof.get("proof")
    require(
        isinstance(proof_binding, dict) and proof_binding.get("tree_digest") == release_tree,
        "post-build proof is bound to different Network release bytes",
    )
    require(
        isinstance(seed_binding, dict)
        and seed_binding.get("release_tree_digest") == binding.release_tree,
        "post-build proof used different Seed release bytes",
    )
    require(
        seed_binding.get("operator") == "ObserveUnknown"
        and seed_binding.get("evidence_relation") == "observation.evidence_digest",
        "post-build proof Seed observation binding drift",
    )
    require(
        seed_binding.get("authority_owner") == "TARGET_LOCAL_SEED",
        "post-build proof changed Seed authority ownership",
    )
    require(
        isinstance(proof_subject, dict) and proof_subject.get("final_theorem") == FINAL_THEOREM,
        "post-build Network final theorem mismatch",
    )
    require(
        isinstance(proof_subject.get("obligations_proved"), int)
        and proof_subject["obligations_proved"] > 0,
        "post-build Network proof obligation count missing",
    )
    assembled = release_root / "formal/AssembledNetwork.tla"
    assembled_binding = proof_binding.get("assembled_formal")
    require(isinstance(assembled_binding, dict), "post-build assembled Network binding missing")
    require(
        assembled_binding.get("sha256") == sha256(assembled),
        "post-build theorem used different assembled Network bytes",
    )
    require(
        proof.get("semantic_delta") == "NONE" and proof.get("status") == "PASS",
        "post-build Network assurance not admitted",
    )

    require(
        airgap.get("document_type") == "aset-network-python-companion-airgap-evidence",
        "air-gap evidence type mismatch",
    )
    require(
        airgap.get("profile_tree_digest") == profiles_tree,
        "air-gap verified a different Network profile tree",
    )
    require(airgap.get("profile_tree_unchanged") is True, "air-gap mutated Network profile tree")
    inputs = airgap.get("inputs")
    require(isinstance(inputs, dict), "air-gap input binding missing")
    seed_python = profiles_root / "base/seed/python/aset_seed_alpha4.py"
    network_python = profiles_root / "python/aset_network_alpha4.py"
    require(
        inputs.get("seed_python", {}).get("sha256") == sha256(seed_python),
        "air-gap Seed Python base mismatch",
    )
    require(
        inputs.get("network_python", {}).get("sha256") == sha256(network_python),
        "air-gap Network Python bytes mismatch",
    )
    require(
        sha256(seed_python) == binding.companions["PYTHON"][1],
        "Network Python extension is not based on exact Seed Python companion",
    )
    coverage = airgap.get("coverage")
    require(isinstance(coverage, dict), "Network Python air-gap coverage missing")
    require(
        coverage.get("total_cases") == 446,
        "Network Python air-gap structural coverage mismatch",
    )
    require(
        coverage.get("core_identity_sensitivity_cases") == 5
        and coverage.get("composition_identity_sensitivity_cases") == 16
        and coverage.get("federation_identity_sensitivity_cases") == 5
        and coverage.get("sensitivity_cases") == 26
        and coverage.get("grand_total_cases") == 472,
        "Network Python air-gap identity sensitivity coverage mismatch",
    )
    require(airgap.get("status") == "PASS", "Network Python air-gap is not PASS")
    dependencies = airgap.get("assurance_dependencies")
    require(
        isinstance(dependencies, dict)
        and dependencies.get("network_semantic_source") == "NONE"
        and dependencies.get("release_profile_generator") == "NONE"
        and dependencies.get("triangulated_expression_checker") == "NONE"
        and dependencies.get("companion_import_surface") == "RESTRICTED"
        and dependencies.get("companion_file_access") == "MATERIALIZED_PROFILE_TREE_READ_ONLY"
        and dependencies.get("companion_dynamic_builtins") == "DENIED"
        and dependencies.get("companion_filesystem_method_aliasing") == "DENIED"
        and dependencies.get("companion_seed_loader_exec") == "EXACT_SEED_BASE_BYTES_ONLY"
        and dependencies.get("runtime_capability_isolation") == "PASS"
        and dependencies.get("process_isolation") == "NOT_CLAIMED",
        "Network Python air-gap independence boundary drift",
    )

    seed_english = profiles_root / "base/seed/en/Seed.md"
    network_english = profiles_root / "en/Network.md"
    require(
        sha256(seed_english) == binding.companions["ENGLISH"][1],
        "Network English extension is not based on exact Seed English companion",
    )
    require(network_english.is_file(), "Network English companion extension missing")
    base_expressions = profiles_manifest.get("base_expressions")
    require(isinstance(base_expressions, dict), "Network companion base binding missing")
    require(
        base_expressions.get("english", {}).get("sha256") == sha256(seed_english),
        "Network English manifest base mismatch",
    )
    require(
        base_expressions.get("python", {}).get("sha256") == sha256(seed_python),
        "Network Python manifest base mismatch",
    )
    network_expressions = companion_evidence.get("network_expressions")
    require(isinstance(network_expressions, dict), "Network companion expression evidence missing")
    require(
        network_expressions.get("english", {}).get("sha256") == sha256(network_english),
        "Network English companion evidence bytes mismatch",
    )
    require(
        network_expressions.get("python", {}).get("sha256") == sha256(network_python),
        "Network Python companion evidence bytes mismatch",
    )
    require(
        f"Exact Seed English base SHA-256: `{sha256(seed_english)}`"
        in network_english.read_text(encoding="utf-8"),
        "Network English extension does not declare exact Seed English base",
    )

    release_archive_digest, release_archive_paths = archive_tree_digest(
        release_archive, release_root.name
    )
    profiles_archive_digest, profiles_archive_paths = archive_tree_digest(
        profiles_archive, profiles_root.name
    )
    require(release_archive_digest == release_tree, "Network release archive/tree mismatch")
    require(
        profiles_archive_digest == profiles_tree,
        "Network companion archive/tree mismatch",
    )
    require(
        release_archive_paths == tree_paths(release_root),
        "Network release archive file set mismatch",
    )
    require(
        profiles_archive_paths == tree_paths(profiles_root),
        "Network companion archive file set mismatch",
    )

    return {
        "document_type": "aset-network-alpha4-release-admission-certificate",
        "subject_id": "ASET-NETWORK-ALPHA4",
        "version": "0.1.0-alpha.4",
        "semantic_precedence": "NONE",
        "assurance_representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "seed_extension": {
            "release_tree_digest": binding.release_tree,
            "profile_tree_digest": binding.profile_tree,
            "bindings": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
            "seed_redefinition": "ABSENT",
        },
        "release": {
            "tree_digest": release_tree,
            "archive": {
                "path": str(release_archive),
                "sha256": sha256(release_archive),
                "tree_digest": release_archive_digest,
            },
        },
        "profiles": {
            "tree_digest": profiles_tree,
            "archive": {
                "path": str(profiles_archive),
                "sha256": sha256(profiles_archive),
                "tree_digest": profiles_archive_digest,
            },
            "relation": "EXTENSION_OF_EXACT_SEED_COMPANIONS",
        },
        "post_build_formal_assurance": {
            "final_theorem": FINAL_THEOREM,
            "obligations_proved": proof_subject["obligations_proved"],
            "status": "PASS",
        },
        "python_airgap": {
            "structural_cases": coverage["total_cases"],
            "identity_sensitivity_cases": coverage["sensitivity_cases"],
            "grand_total_cases": coverage["grand_total_cases"],
            "runtime_capability_isolation": "PASS",
            "process_isolation": "NOT_CLAIMED",
            "dynamic_builtins": "DENIED",
            "filesystem_method_aliasing": "DENIED",
            "seed_loader_exec": "EXACT_SEED_BASE_BYTES_ONLY",
            "status": "PASS",
        },
        "public_assurance": {
            "identity": "ASET_NETWORK",
            "representation": "0.1.0-alpha.4",
            "assurance_representations": "OPERATIONAL,RELATIONAL,CAUSAL",
            "post_build_formal_assurance": "PASS",
            "companion_relation": "EXTENSION_OF_EXACT_SEED_COMPANIONS",
        },
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--profiles-root", type=Path, required=True)
    parser.add_argument("--proof-evidence", type=Path, required=True)
    parser.add_argument("--airgap-evidence", type=Path, required=True)
    parser.add_argument("--release-archive", type=Path, required=True)
    parser.add_argument("--profiles-archive", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-release-admission-certificate.json",
    )
    args = parser.parse_args()
    try:
        evidence = check_admission(
            args.release_root,
            args.profiles_root,
            args.proof_evidence,
            args.airgap_evidence,
            args.release_archive,
            args.profiles_archive,
        )
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_SEED_BINDINGS=3/3 PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_SEED_REDEFINITION=ABSENT")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_POST_BUILD_TLAPS=PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_ENGLISH_SEED_BASE=EXACT")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_SEED_BASE=EXACT")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_AIRGAP=446/446 PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_AIRGAP_IDENTITY_SENSITIVITY=26/26 PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_AIRGAP_GRAND_TOTAL=472/472 PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_RUNTIME_CAPABILITY_ISOLATION=PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_PYTHON_PROCESS_ISOLATION=NOT_CLAIMED")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_ARCHIVE_BINDING=EXACT")
        print("ALPHA4_NETWORK_PUBLIC_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
        print("ALPHA4_NETWORK_PUBLIC_POST_BUILD_FORMAL_ASSURANCE=PASS")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_CERTIFICATE=PASS")
        return 0
    except (
        json.JSONDecodeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        NetworkReleaseAdmissionError,
    ) as error:
        print(f"ALPHA4_NETWORK_RELEASE_ADMISSION_ERROR={error}")
        print("ALPHA4_NETWORK_RELEASE_ADMISSION_CERTIFICATE=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
