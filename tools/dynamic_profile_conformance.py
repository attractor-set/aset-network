from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
SCHEMA_DIR = CANON / "protocol/schemas"
PROFILE_CONFORMANCE = CANON / "conformance/dynamic-profile-conformance-profile.json"

PROFILE_CONTEXT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/\-]*$")
PROFILE_CONTEXT_ID_MIN = 3
PROFILE_CONTEXT_ID_MAX = 256
JCS_SAFE_INTEGER_MAX = 9_007_199_254_740_991


def _key_order(value: str) -> bytes:
    return value.encode("utf-16-be", errors="strict")


def _canonical_text(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        # Profile wire schemas contain no alternate Unicode normalization rule;
        # JCS preserves strings and applies JSON escaping only.
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        if abs(value) > JCS_SAFE_INTEGER_MAX:
            raise ValueError("integer outside the profile JCS safe range")
        return str(value)
    if isinstance(value, float):
        raise ValueError("profile wire objects do not permit floating-point numbers")
    if isinstance(value, list):
        return "[" + ",".join(_canonical_text(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        items = []
        for key in sorted(value, key=_key_order):
            items.append(f"{_canonical_text(key)}:{_canonical_text(value[key])}")
        return "{" + ",".join(items) + "}"
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def jcs_bytes(value: Any) -> bytes:
    return _canonical_text(value).encode("utf-8", errors="strict")


def content_digest(value: dict[str, Any], digest_field: str) -> str:
    payload = dict(value)
    payload.pop(digest_field, None)
    return "sha256:" + hashlib.sha256(jcs_bytes(payload)).hexdigest()


def _schema_registry() -> tuple[Registry, dict[str, dict[str, Any]]]:
    resources = []
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(data)
        resources.append((data["$id"], Resource.from_contents(data)))
        schemas[path.name] = data
    return Registry().with_resources(resources), schemas


def validate_wire_object(object_type: str, value: dict[str, Any]) -> tuple[bool, str]:
    registry, schemas = _schema_registry()
    if object_type == "PROFILE_DEFINITION":
        schema_name = "profile-definition.schema.json"
        digest_field = "profile_digest"
        mismatch_code = "PROFILE_DIGEST_MISMATCH"
    elif object_type == "PROFILE_BINDING":
        schema_name = "profile-binding.schema.json"
        digest_field = "binding_digest"
        mismatch_code = "PROFILE_BINDING_DIGEST_MISMATCH"
    else:
        return False, "UNKNOWN_PROFILE_OBJECT_TYPE"

    validator = Draft202012Validator(schemas[schema_name], registry=registry)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        return False, f"{object_type}_SCHEMA_INVALID"
    if value[digest_field] != content_digest(value, digest_field):
        return False, mismatch_code
    return True, f"{object_type}_VALID"


def project_seed_binding(binding: dict[str, Any]) -> dict[str, Any]:
    projected: dict[str, Any] = {
        "context_id": binding["target_context_id"],
        "state_root": binding["target_state_root"],
        "question_digest": binding["profile_digest"],
        "policy_epoch": binding["target_policy_epoch"],
        "scope": binding["seed_scope"],
    }
    projected["binding_digest"] = content_digest(projected, "binding_digest")
    return projected


def seed_projection_shape_valid(projected: dict[str, Any]) -> bool:
    context_id = projected.get("context_id")
    if not isinstance(context_id, str):
        return False
    if not (PROFILE_CONTEXT_ID_MIN <= len(context_id) <= PROFILE_CONTEXT_ID_MAX):
        return False
    if PROFILE_CONTEXT_ID_RE.fullmatch(context_id) is None:
        return False
    epoch = projected.get("policy_epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 0:
        return False
    if epoch > JCS_SAFE_INTEGER_MAX:
        return False
    scope = projected.get("scope")
    if not isinstance(scope, list) or not scope or len(scope) != len(set(scope)):
        return False
    if any(not isinstance(item, str) or not 1 <= len(item) <= 300 for item in scope):
        return False
    digest_re = re.compile(r"^sha256:[0-9a-f]{64}$")
    return all(
        isinstance(projected.get(field), str)
        and digest_re.fullmatch(projected[field]) is not None
        for field in ("state_root", "question_digest", "binding_digest")
    )


def evaluate_activation(
    binding: dict[str, Any], seed_binding: dict[str, Any], seed_resolution: str
) -> tuple[bool, str]:
    ok, code = validate_wire_object("PROFILE_BINDING", binding)
    if not ok:
        return False, code
    projected = project_seed_binding(binding)
    if not seed_projection_shape_valid(projected):
        return False, "SEED_PROJECTION_INVALID"
    if seed_binding != projected:
        return False, "SEED_BINDING_MISMATCH"
    if seed_resolution != "ALLOW":
        return False, "TARGET_LOCAL_SEED_ALLOW_REQUIRED"
    return True, "PROFILE_APPLICABLE"


def execute_case(case: dict[str, Any]) -> dict[str, Any]:
    operation = case["operation"]
    if operation == "VALIDATE_PROFILE_DEFINITION":
        accepted, code = validate_wire_object("PROFILE_DEFINITION", case["object"])
        return {"accepted": accepted, "code": code}
    if operation == "VALIDATE_PROFILE_BINDING":
        accepted, code = validate_wire_object("PROFILE_BINDING", case["object"])
        return {"accepted": accepted, "code": code}
    if operation == "EVALUATE_PROFILE_APPLICABILITY":
        accepted, code = evaluate_activation(
            case["binding"], case["seed_binding"], case["seed_resolution"]
        )
        return {"accepted": accepted, "code": code}
    raise ValueError(f"unknown dynamic-profile conformance operation: {operation}")


def load_profile_conformance() -> dict[str, Any]:
    return json.loads(PROFILE_CONFORMANCE.read_text(encoding="utf-8"))


def run_profile_conformance() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    profile = load_profile_conformance()
    failures = []
    for item in profile["cases"]:
        path = ROOT / item["path"]
        case = json.loads(path.read_text(encoding="utf-8"))
        actual = execute_case(case)
        if actual != case["expected"]:
            failures.append((case["case_id"], case["expected"], actual))
    return failures
