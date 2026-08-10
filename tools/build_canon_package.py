from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.build_formal_relation import main as build_formal_relation

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
PACKAGE = CANON / "CANON_PACKAGE.json"
UPSTREAM_BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"
CANON_SUFFIXES = {".json", ".tla", ".cfg"}
CANON_TOP_LEVEL = {"assurance", "conformance", "formal", "profiles", "protocol", "source"}


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def included_in_canon(path: Path) -> bool:
    if path == PACKAGE or path.suffix not in CANON_SUFFIXES:
        return False
    relative = path.relative_to(CANON)
    if not relative.parts or relative.parts[0] not in CANON_TOP_LEVEL:
        return False
    # Formal source is intentionally flat. TLC runtime metadata must never become
    # part of the normative package merely because model checking ran in-place.
    if relative.parts[0] == "formal" and len(relative.parts) != 2:
        return False
    return True


def build_package() -> dict[str, object]:
    paths = [
        path for path in sorted(CANON.rglob("*")) if path.is_file() and included_in_canon(path)
    ]
    paths.append(UPSTREAM_BINDING)
    files = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)} for path in sorted(paths)
    ]
    package: dict[str, object] = {
        "document_type": "aset-extension-canon-package",
        "schema_version": 1,
        "extension_id": "ASET-NETWORK-EXTENSION",
        "extension_version": "0.1.0-alpha.3",
        "canon_id": "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA3",
        "normative_source": "extension/canonical/source/network-extension-model.json",
        "upstream_binding": "upstream/ASET_SEED_BINDING.json",
        "implementation_precedence": "NONE",
        "files": files,
    }
    package["package_digest"] = "sha256:" + hashlib.sha256(canonical_bytes(package)).hexdigest()
    return package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    relation_status = build_formal_relation(["--check"] if args.check else [])
    if relation_status != 0:
        print("CANON_PACKAGE_CHECK=FAIL" if args.check else "CANON_PACKAGE_BUILD=FAIL")
        return relation_status

    package = build_package()
    rendered = canonical_bytes(package)
    files = package["files"]
    assert isinstance(files, list)

    if args.check:
        if not PACKAGE.is_file() or PACKAGE.read_bytes() != rendered:
            print("CANON_PACKAGE_CHECK=FAIL")
            return 1
        print(f"OK: package files={len(files)}")
        print(f"OK: package digest={package['package_digest']}")
        print("CANON_PACKAGE_CHECK=PASS")
        return 0

    PACKAGE.write_bytes(rendered)
    print(f"OK: wrote {PACKAGE.relative_to(ROOT)} with {len(files)} files")
    print(f"OK: package digest={package['package_digest']}")
    print("CANON_PACKAGE_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
