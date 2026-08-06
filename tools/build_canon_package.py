from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
PACKAGE = CANON / "CANON_PACKAGE.json"
UPSTREAM_BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    paths = [path for path in sorted(CANON.rglob("*")) if path.is_file() and path != PACKAGE]
    paths.append(UPSTREAM_BINDING)
    files = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}
        for path in sorted(paths)
    ]
    package = {
        "document_type": "aset-extension-canon-package",
        "schema_version": 1,
        "extension_id": "ASET-NETWORK-EXTENSION",
        "extension_version": "0.1.0-alpha.1",
        "canon_id": "ASET-NETWORK-EXTENSION-CANON-0.1-ALPHA1",
        "normative_source": "extension/canonical/source/network-extension-model.json",
        "upstream_binding": "upstream/ASET_SEED_BINDING.json",
        "implementation_precedence": "NONE",
        "files": files,
    }
    package["package_digest"] = "sha256:" + hashlib.sha256(canonical_bytes(package)).hexdigest()
    PACKAGE.write_bytes(canonical_bytes(package))
    print(f"OK: wrote {PACKAGE.relative_to(ROOT)} with {len(files)} files")
    print(f"OK: package digest={package['package_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
