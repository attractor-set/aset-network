from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ROOT_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "NOTICE",
    "README.md",
    "pyproject.toml",
    "requirements-ci.txt",
}
ALLOWED_ROOT_DIRS = {
    ".github",
    "history",
    "network",
    "tests",
    "theory",
    "tools",
    "upstream",
}
EXPECTED_THEORY_FILES = {
    "theory/network-seed-reflection/formal/NetworkExtension.tla",
    "theory/network-seed-reflection/formal/NetworkExtensionSeedRefinement.tla",
    "theory/network-seed-reflection/formal/NetworkExtensionSeedRefinementProofs.tla",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args, "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(result.returncode == 0, f"git surface query failed: {' '.join(args)}")
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def repository_paths() -> set[str]:
    paths = git_paths("ls-files", "--cached", "--others", "--exclude-standard")
    deleted = git_paths("diff", "--name-only", "--diff-filter=D")
    deleted |= git_paths("diff", "--cached", "--name-only", "--diff-filter=D")
    return paths - deleted


def relative_files(path: Path) -> set[str]:
    prefix = path.relative_to(ROOT).as_posix().rstrip("/") + "/"
    return {item for item in repository_paths() if item.startswith(prefix)}


def validate_root_surface() -> None:
    paths = repository_paths()
    files = {path for path in paths if "/" not in path}
    dirs = {path.split("/", 1)[0] for path in paths if "/" in path}
    file_drift = sorted(files ^ ALLOWED_ROOT_FILES)
    require(files == ALLOWED_ROOT_FILES, f"root file surface drift: {file_drift}")
    dir_drift = sorted(dirs ^ ALLOWED_ROOT_DIRS)
    require(dirs == ALLOWED_ROOT_DIRS, f"root directory surface drift: {dir_drift}")


def validate_single_readme() -> None:
    readmes = sorted(
        path for path in repository_paths() if Path(path).name.lower().startswith("readme")
    )
    require(readmes == ["README.md"], f"README surface must be singular: {readmes}")


def validate_active_network_line() -> None:
    network = ROOT / "network"
    children = {path.split("/", 2)[1] for path in repository_paths() if path.startswith("network/")}
    require(children == {"alpha4"}, "Network must contain exactly one active Alpha4 line")
    require((network / "alpha4/NETWORK.aset").is_file(), "current Alpha4 subject missing")
    subject = (network / "alpha4/NETWORK.aset").read_text(encoding="utf-8")
    require("ALPHA3-COMPATIBILITY NONE" in subject, "historical compatibility boundary drift")


def validate_history_and_theory() -> None:
    history = (ROOT / "history/REFERENCES.aset").read_text(encoding="utf-8")
    require("ASET-HISTORY 1" in history, "history header missing")
    require("STATE NETWORK-0.1.0-ALPHA.3" in history, "Alpha3 historical reference missing")
    require(
        (
            "PROOF NETWORK-0.1.0-ALPHA.3 SEED-REFLECTION "
            "ASET-NETWORK-SEED-REFINEMENT-TLAPS-V2 35 MECHANICALLY_PROVED"
        )
        in history,
        "retained reflection proof reference missing",
    )
    theory_files = relative_files(ROOT / "theory")
    theory_drift = sorted(theory_files ^ EXPECTED_THEORY_FILES)
    require(theory_files == EXPECTED_THEORY_FILES, f"theory surface drift: {theory_drift}")


def validate_upstream_surface() -> None:
    upstream_files = relative_files(ROOT / "upstream")
    require(
        upstream_files == {"upstream/ASET_SEED_ALPHA4_BINDING.aset"},
        f"upstream surface drift: {sorted(upstream_files)}",
    )


def validate_verification_surface() -> None:
    workflows = relative_files(ROOT / ".github/workflows")
    require(
        workflows == {".github/workflows/verify.yml"},
        f"workflow surface drift: {sorted(workflows)}",
    )


def validate_attribution() -> None:
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    require("Copyright 2026 Dzmitry Prychyna" in notice, "copyright notice drift")
    require("Attractor Set" in notice, "public author identity missing")
    require(
        "Original author and copyright holder: Dzmitry Prychyna." in notice,
        "original authorship notice missing",
    )
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    require(
        "family-names: Prychyna" in citation and "given-names: Dzmitry" in citation,
        "citation authorship drift",
    )
    require('version: "0.1.0-alpha.4"' in citation, "citation version drift")


def main() -> int:
    validate_root_surface()
    validate_single_readme()
    validate_active_network_line()
    validate_history_and_theory()
    validate_upstream_surface()
    validate_verification_surface()
    validate_attribution()
    print("REPOSITORY_ACTIVE_SURFACE=MINIMAL")
    print("REPOSITORY_LEGACY_SEMANTIC_SURFACE=ABSENT")
    print("REPOSITORY_HISTORY_REFERENCES=PASS")
    print("REPOSITORY_COPYRIGHT_NOTICE=PASS")
    print("REPOSITORY_SINGLE_README=PASS")
    print("REPOSITORY_SINGLE_ACTIVE_NETWORK_LINE=ALPHA4")
    print("REPOSITORY_SINGLE_VERIFICATION_WORKFLOW=PASS")
    print("ASET_NETWORK_REPOSITORY_MINIMAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
