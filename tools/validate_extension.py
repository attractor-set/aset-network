from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    package = json.loads((CANON / "CANON_PACKAGE.json").read_text(encoding="utf-8"))
    declared_digest = package.pop("package_digest")
    actual_package_digest = "sha256:" + hashlib.sha256(canonical_bytes(package)).hexdigest()
    if actual_package_digest != declared_digest:
        raise SystemExit("package self-digest mismatch")
    package["package_digest"] = declared_digest

    for item in package["files"]:
        path = ROOT / item["path"]
        if not path.is_file():
            raise SystemExit(f"missing package file: {item['path']}")
        if sha(path) != item["sha256"]:
            raise SystemExit(f"digest mismatch: {item['path']}")

    resources = []
    by_name = {}
    schema_dir = CANON / "protocol/schemas"
    for path in schema_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(data)
        resources.append((data["$id"], Resource.from_contents(data)))
        by_name[path.name] = data
    registry = Registry().with_resources(resources)

    validator = Draft202012Validator(by_name["conformance-case.schema.json"], registry=registry)
    for path in (CANON / "conformance/cases").rglob("*.json"):
        validator.validate(json.loads(path.read_text(encoding="utf-8")))

    print(f"OK: package files={len(package['files'])}")
    print(f"OK: package digest={declared_digest}")
    print("OK: schemas valid")
    print("OK: conformance cases valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
