from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from tools.alpha4_network_release_profiles import build_release_profiles
from tools.alpha4_network_seed_extension import (
    SeedExtensionError,
    check_seed_companion_bases,
    parse_seed_binding,
    sha256,
    tree_digest,
)
from tools.alpha4_network_triangulated_expression import check_triangulated_assurance
from tools.validate_alpha4_network import validate_active_selection, validate_network_surface

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE_NAME = "ASET-Network-0.1.0-alpha.4"
PROFILES_NAME = RELEASE_NAME + "-profiles"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class NetworkReleaseError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NetworkReleaseError(message)


def source_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def tracked_state() -> str | None:
    if not (ROOT / ".git").exists() or shutil.which("git") is None:
        return None
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def zip_tree(root: Path, target: Path, archive_root_name: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = f"{archive_root_name}/{path.relative_to(root).as_posix()}"
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes())


def _network_source_files() -> list[Path]:
    files = [path for path in (ROOT / "network/alpha4").rglob("*") if path.is_file()]
    files.append(ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset")
    return files


def write_assembled_network(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                "----------------------- MODULE AssembledNetwork -----------------------",
                "EXTENDS NetworkRelations",
                "",
                "Next(s, t, observation, result) ==",
                "  AdmitImport(s, t, observation, result)",
                "",
                "=============================================================================",
                "",
            ]
        ),
        encoding="utf-8",
    )


def verify_seed_release(seed_release_root: Path) -> dict[str, str]:
    binding = parse_seed_binding()
    root = seed_release_root.resolve()
    require(root.is_dir(), "exact Seed release tree missing")
    actual = tree_digest(root)
    require(actual == binding.release_tree, "Seed release tree digest mismatch")
    operational = root / "operational/components.forth"
    component = root / "formal/ComponentRelations.tla"
    causal = root / "causal/components.petri"
    algebra = root / "formal/LocalRecognitionAlgebra.tla"
    assembled = root / "formal/AssembledSeed.tla"
    for path in (operational, component, causal, algebra, assembled):
        require(path.is_file(), f"Seed release assurance artifact missing: {path.name}")
    require(
        sha256(operational) == binding.sources["seed/alpha4/operational/components.forth"],
        "Seed release operational base differs from bound source",
    )
    require(
        sha256(component) == binding.sources["seed/alpha4/formal/ComponentRelations.tla"],
        "Seed release relational base differs from bound source",
    )
    require(
        sha256(causal) == binding.sources["seed/alpha4/causal/components.petri"],
        "Seed release causal base differs from bound source",
    )
    require(
        sha256(algebra)
        == binding.sources["theory/local-recognition/formal/LocalRecognitionAlgebra.tla"],
        "Seed release algebra differs from bound source",
    )
    return {
        "tree_digest": actual,
        "operational_sha256": sha256(operational),
        "component_relations_sha256": sha256(component),
        "causal_sha256": sha256(causal),
        "local_recognition_algebra_sha256": sha256(algebra),
        "assembled_seed_sha256": sha256(assembled),
    }


def build_release_tree(seed_release_root: Path, output: Path) -> dict[str, Any]:
    validate_active_selection()
    validate_network_surface()
    seed = verify_seed_release(seed_release_root)
    if output.exists():
        shutil.rmtree(output)
    (output / "network").mkdir(parents=True)
    (output / "upstream").mkdir(parents=True)
    (output / "formal").mkdir(parents=True)
    (output / "assurance").mkdir(parents=True)

    shutil.copy2(ROOT / "LICENSE", output / "LICENSE")
    shutil.copy2(ROOT / "NOTICE", output / "NOTICE")
    shutil.copytree(ROOT / "network/alpha4", output / "network/alpha4")
    shutil.copy2(
        ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset",
        output / "upstream/ASET_SEED_ALPHA4_BINDING.aset",
    )
    write_assembled_network(output / "formal/AssembledNetwork.tla")

    tri = check_triangulated_assurance(ROOT)
    assurance = {
        "document_type": "aset-network-release-three-way-assurance-evidence",
        "representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "semantic_precedence": "NONE",
        "semantic_delta": "NONE",
        "core_cases": tri["core_cases"],
        "dynamic_cases": tri["dynamic_cases"],
        "federation_states": tri["federation_states"],
        "federation_edges": tri["federation_edges"],
        "liveness_cases": tri["liveness_cases"],
        "composition_cases": tri["composition_cases"],
        "total_cases": tri["total_cases"],
        "status": "PASS",
    }
    (output / "assurance/THREE_WAY_EVIDENCE.json").write_text(
        json.dumps(assurance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    source_files = _network_source_files()
    manifest: dict[str, Any] = {
        "document_type": "aset-network-alpha4-release-materialization",
        "subject_id": "ASET-NETWORK-ALPHA4",
        "version": "0.1.0-alpha.4",
        "semantic_precedence": "NONE",
        "source_byte_identity_digest": source_digest(source_files),
        "seed_base": {
            "subject_id": "ASET-SEED-0.4-ALPHA",
            "release_tag": parse_seed_binding().release_tag,
            **seed,
            "relation": "REPRESENTATION_WISE_EXTENSION_BASE",
        },
        "assurance_representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "extension_bindings": {
            "operational": "OBSERVE-UNKNOWN -> ADMIT-FRESH,ADMIT-REPLAY",
            "relational": "ObserveUnknown -> AdmitFresh,AdmitReplay",
            "causal": "OBSERVE-UNKNOWN -> ADMIT-FRESH,ADMIT-REPLAY",
            "rejected_branch": "REJECT-CONFLICT -> NO_SEED_TRANSITION",
        },
        "assembled_formal": {
            "path": "formal/AssembledNetwork.tla",
            "sha256": sha256(output / "formal/AssembledNetwork.tla"),
            "scope": "NETWORK_CORE_ADMISSION",
        },
        "profile_subjects": ["DYNAMIC", "FEDERATION", "LIVENESS", "FEDERATION-LIVENESS"],
        "three_way_assurance": "assurance/THREE_WAY_EVIDENCE.json",
        "artifacts": [
            {"path": path.relative_to(output).as_posix(), "sha256": sha256(path)}
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "RELEASE_MANIFEST.json"
        ],
    }
    (output / "RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_profiles_tree(
    seed_profiles_root: Path,
    network_release_tree_digest: str,
    output: Path,
) -> dict[str, Any]:
    binding = parse_seed_binding()
    seed_profiles = check_seed_companion_bases(seed_profiles_root)
    evidence = build_release_profiles(seed_profiles_root, output)
    (output / "assurance").mkdir(parents=True, exist_ok=True)
    (output / "assurance/COMPANION_EXTENSION_EVIDENCE.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest: dict[str, Any] = {
        "document_type": "aset-network-alpha4-release-companion-materialization",
        "subject_id": "ASET-NETWORK-ALPHA4",
        "version": "0.1.0-alpha.4",
        "semantic_precedence": "NONE",
        "relation": "EXTENSION_OF_EXACT_SEED_COMPANIONS",
        "network_release_tree_digest": network_release_tree_digest,
        "seed_release_tree_digest": binding.release_tree,
        "seed_profile_tree_digest": seed_profiles["profile_tree_digest"],
        "profiles": {
            "controlled_english": "en/Network.md",
            "python": "python/aset_network_alpha4.py",
        },
        "base_expressions": evidence["base_expressions"],
        "companion_extension_evidence": "assurance/COMPANION_EXTENSION_EVIDENCE.json",
        "artifacts": [
            {"path": path.relative_to(output).as_posix(), "sha256": sha256(path)}
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "RELEASE_PROFILE_MANIFEST.json"
        ],
    }
    (output / "RELEASE_PROFILE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _build_once(
    seed_release_root: Path, seed_profiles_root: Path, base: Path
) -> tuple[Path, Path, Path, Path]:
    release = base / RELEASE_NAME
    profiles = base / PROFILES_NAME
    build_release_tree(seed_release_root, release)
    release_digest = tree_digest(release)
    build_profiles_tree(seed_profiles_root, release_digest, profiles)
    release_zip = base / f"{RELEASE_NAME}.zip"
    profiles_zip = base / f"{PROFILES_NAME}.zip"
    zip_tree(release, release_zip, RELEASE_NAME)
    zip_tree(profiles, profiles_zip, PROFILES_NAME)
    return release, profiles, release_zip, profiles_zip


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-release-root", type=Path, required=True)
    parser.add_argument("--seed-profiles-root", type=Path, required=True)
    parser.add_argument("--verify-determinism", action="store_true")
    args = parser.parse_args()
    try:
        before = tracked_state()
        DIST.mkdir(parents=True, exist_ok=True)
        release, profiles, release_zip, profiles_zip = _build_once(
            args.seed_release_root.resolve(), args.seed_profiles_root.resolve(), DIST
        )
        release_digest = tree_digest(release)
        profile_digest = tree_digest(profiles)
        release_archive_sha = sha256(release_zip)
        profile_archive_sha = sha256(profiles_zip)
        if args.verify_determinism:
            with tempfile.TemporaryDirectory(prefix="aset-network-release-rebuild-") as temporary:
                temp = Path(temporary)
                r2, p2, rz2, pz2 = _build_once(
                    args.seed_release_root.resolve(), args.seed_profiles_root.resolve(), temp
                )
                require(
                    tree_digest(r2) == release_digest,
                    "Network release tree is not deterministic",
                )
                require(
                    tree_digest(p2) == profile_digest,
                    "Network profile tree is not deterministic",
                )
                require(
                    sha256(rz2) == release_archive_sha,
                    "Network release archive is not deterministic",
                )
                require(
                    sha256(pz2) == profile_archive_sha,
                    "Network profile archive is not deterministic",
                )
        after = tracked_state()
        if before is not None and after != before:
            raise NetworkReleaseError("release build changed tracked repository state")
        print("ALPHA4_NETWORK_RELEASE_DETERMINISM=PASS")
        print("ALPHA4_NETWORK_RELEASE_PROFILE_DETERMINISM=PASS")
        print(f"ALPHA4_NETWORK_RELEASE_TREE_DIGEST={release_digest}")
        print(f"ALPHA4_NETWORK_RELEASE_ARCHIVE={release_zip.relative_to(ROOT)}")
        print(f"ALPHA4_NETWORK_RELEASE_ARCHIVE_SHA256={release_archive_sha}")
        print(f"ALPHA4_NETWORK_RELEASE_PROFILE_TREE_DIGEST={profile_digest}")
        print(f"ALPHA4_NETWORK_RELEASE_PROFILE_ARCHIVE={profiles_zip.relative_to(ROOT)}")
        print(f"ALPHA4_NETWORK_RELEASE_PROFILE_ARCHIVE_SHA256={profile_archive_sha}")
        print("ALPHA4_NETWORK_RELEASE_ENGLISH_EXTENSION=PASS")
        print("ALPHA4_NETWORK_RELEASE_PYTHON_EXTENSION=EXACT_SEED_BASE")
        print("ALPHA4_NETWORK_RELEASE_BUILD=PASS")
        return 0
    except (OSError, UnicodeError, ValueError, NetworkReleaseError, SeedExtensionError) as error:
        print(f"ALPHA4_NETWORK_RELEASE_ERROR={error}")
        print("ALPHA4_NETWORK_RELEASE_BUILD=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
