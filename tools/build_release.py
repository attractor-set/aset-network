from __future__ import annotations

import argparse
import hashlib
import stat
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ARCHIVE = DIST / "ASET-Network-Extension-Repository-Snapshot.zip"
FIXED = (1980, 1, 1, 0, 0, 0)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".tlacache",
    ".tooling",
    "states",
    "dist",
    "build",
}


def included(path: Path) -> bool:
    if path.as_posix() == ".coverage":
        return False
    if any(part.endswith(".egg-info") for part in path.parts):
        return False
    return not any(part in EXCLUDED_PARTS for part in path.parts)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def tracked_paths(ref: str) -> list[Path]:
    raw = git_bytes("ls-tree", "-r", "--name-only", "-z", ref)
    paths = [Path(item.decode("utf-8")) for item in raw.split(b"\0") if item]
    return [path for path in paths if included(path)]


def committed_bytes(ref: str, path: Path) -> bytes:
    return git_bytes("show", f"{ref}:{path.as_posix()}")


def build_archive(output: Path, ref: str) -> None:
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for relative in sorted(
            tracked_paths(ref),
            key=lambda item: (Path("ASET-Network-Extension") / item).as_posix(),
        ):
            info = zipfile.ZipInfo(
                (Path("ASET-Network-Extension") / relative).as_posix(),
                FIXED,
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, committed_bytes(ref, relative))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-determinism", action="store_true")
    args = parser.parse_args(argv)

    DIST.mkdir(parents=True, exist_ok=True)
    ref = git_text("rev-parse", "HEAD")
    build_archive(ARCHIVE, ref)
    digest = sha256_file(ARCHIVE)

    if args.verify_determinism:
        comparison = DIST / ".ASET-Network-Extension-Repository-Snapshot.rebuild.zip"
        try:
            build_archive(comparison, ref)
            rebuild_digest = sha256_file(comparison)
        finally:
            if comparison.exists():
                comparison.unlink()
        if rebuild_digest != digest:
            print(f"INPI_DEPOSIT_REBUILD_SHA256={rebuild_digest}")
            print("INPI_DEPOSIT_DETERMINISTIC_REBUILD=FAIL")
            return 1
        print("INPI_DEPOSIT_DETERMINISTIC_REBUILD=PASS")

    checksum = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
    checksum.write_text(
        f"{digest} {ARCHIVE.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"INPI_DEPOSIT_SOURCE_COMMIT={ref}")
    print(f"INPI_DEPOSIT_ARCHIVE={ARCHIVE}")
    print(f"INPI_DEPOSIT_SHA256={digest}")
    print("INPI_DEPOSIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
