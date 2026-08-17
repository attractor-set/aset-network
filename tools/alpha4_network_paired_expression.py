from __future__ import annotations

import itertools
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha4_network_relational_expression import relational_admit_from_source

ROOT = Path(__file__).resolve().parents[1]
FORTH = ROOT / "network/alpha4/operational/components.forth"

EXPECTED_WORDS = {
    "ADMIT-FRESH": ("EXACT-IMPORT?", "FRESH-ID?", "ADD-IMPORT", "IMPORT-ADMITTED"),
    "ADMIT-REPLAY": (
        "EXACT-IMPORT?",
        "EXACT-REPLAY?",
        "KEEP-IMPORTS",
        "IDEMPOTENT-REPLAY",
    ),
    "REJECT-CONFLICT": (
        "EXACT-IMPORT?",
        "CONFLICTING-ID?",
        "KEEP-IMPORTS",
        "IDENTIFIER-CONFLICT",
    ),
}


EXPECTED_STACK_EFFECTS = {
    "ADMIT-FRESH": (("imports", "observation"), ("imports", "result")),
    "ADMIT-REPLAY": (("imports", "observation"), ("imports", "result")),
    "REJECT-CONFLICT": (("imports", "observation"), ("imports", "result")),
}

OBSERVATION_FIELDS = {
    "import_id",
    "source_context",
    "target_context",
    "evidence_digest",
}


def parse_operational_words(path: Path = FORTH) -> dict[str, tuple[str, ...]]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r":\s+(?P<word>[A-Z0-9-]+)\s+"
        r"\(\s*(?P<inputs>.*?)\s*--\s*(?P<outputs>.*?)\s*\)\s+"
        r"(?P<body>.*?)\s*;"
    )
    matches = list(pattern.finditer(text))
    words = {match.group("word"): tuple(match.group("body").split()) for match in matches}
    stacks = {
        match.group("word"): (
            tuple(match.group("inputs").split()),
            tuple(match.group("outputs").split()),
        )
        for match in matches
    }
    if words != EXPECTED_WORDS:
        raise RuntimeError(f"restricted operational vocabulary mismatch: {words!r}")
    if stacks != EXPECTED_STACK_EFFECTS:
        raise RuntimeError(f"restricted operational stack contract mismatch: {stacks!r}")
    return words


def exact_observation(value: dict[str, Any]) -> bool:
    if set(value) != OBSERVATION_FIELDS:
        return False
    if not all(isinstance(value[key], str) and value[key] for key in OBSERVATION_FIELDS):
        return False
    digest = value["evidence_digest"]
    return bool(re.fullmatch(r"sha256:[0-9a-f]{64}", digest))


def _same_id(imports: list[dict[str, Any]], observation: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in imports if item["import_id"] == observation["import_id"]]


def operational_admit(
    imports: list[dict[str, Any]], observation: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parse_operational_words()
    if not exact_observation(observation):
        return deepcopy(imports), _result(False, "INVALID_IMPORT", False)
    same_id = _same_id(imports, observation)
    if not same_id:
        new_state = deepcopy(imports)
        new_state.append(deepcopy(observation))
        return new_state, _result(True, "IMPORT_ADMITTED", True)
    if observation in same_id:
        return deepcopy(imports), _result(True, "IDEMPOTENT_REPLAY", False)
    return deepcopy(imports), _result(False, "IDENTIFIER_CONFLICT", False)


def relational_admit(
    imports: list[dict[str, Any]], observation: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not exact_observation(observation):
        return deepcopy(imports), _result(False, "INVALID_IMPORT", False)
    return relational_admit_from_source(imports, observation)


def field_sensitivity_check() -> int:
    digests = ["sha256:" + (ch * 64) for ch in ("0", "1")]
    base = {
        "import_id": "i0",
        "source_context": "s0",
        "target_context": "t0",
        "evidence_digest": digests[0],
    }
    variants = []
    replacements = {
        "import_id": "i1",
        "source_context": "s1",
        "target_context": "t1",
        "evidence_digest": digests[1],
    }
    for field, replacement in replacements.items():
        value = dict(base)
        value[field] = replacement
        variants.append((field, value))

    checks = 0
    for field, variant in variants:
        state = [deepcopy(base)]
        operational = operational_admit(state, variant)
        relational = relational_admit(state, variant)
        if operational != relational:
            raise RuntimeError(f"field sensitivity mismatch: {field}")
        checks += 1

    first = {**base, "import_id": "i1"}
    second = deepcopy(base)
    candidate = deepcopy(second)
    state = [first, second]
    operational = operational_admit(state, candidate)
    relational = relational_admit(state, candidate)
    if operational != relational or operational[1]["code"] != "IDEMPOTENT_REPLAY":
        raise RuntimeError("multi-record second-position identity sensitivity mismatch")
    checks += 1
    return checks


def _result(accepted: bool, code: str, changed: bool) -> dict[str, Any]:
    if accepted:
        recognition = "UNKNOWN"
        effect_permitted = False
    else:
        recognition = "NOT_APPLICABLE"
        effect_permitted = False
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "seed_projection": {
            "recognition": recognition,
            "effect_permitted": effect_permitted,
        },
    }


def bounded_pairing_check() -> tuple[int, int]:
    digests = ["sha256:" + (ch * 64) for ch in ("0", "1")]
    observations = [
        {
            "import_id": import_id,
            "source_context": source,
            "target_context": target,
            "evidence_digest": digest,
        }
        for import_id, source, target, digest in itertools.product(
            ("i0", "i1"), ("s0", "s1"), ("t0", "t1"), digests
        )
    ]
    states: list[list[dict[str, Any]]] = [[]]
    states.extend([[deepcopy(item)] for item in observations])
    checks = 0
    accepted = 0
    for state in states:
        for observation in observations:
            op_state, op_result = operational_admit(state, observation)
            rel_state, rel_result = relational_admit(state, observation)
            if op_state != rel_state or op_result != rel_result:
                raise RuntimeError(
                    f"paired expression mismatch: state={state!r} observation={observation!r}"
                )
            if op_result["accepted"]:
                accepted += 1
                projection = op_result["seed_projection"]
                if projection != {"recognition": "UNKNOWN", "effect_permitted": False}:
                    raise RuntimeError("accepted admission crossed Seed recognition boundary")
            checks += 1
    return checks, accepted


def main() -> int:
    parse_operational_words()
    checks, accepted = bounded_pairing_check()
    sensitivity = field_sensitivity_check()
    print("ALPHA4_NETWORK_OPERATIONAL_WORDS=3/3 PASS")
    print(f"ALPHA4_NETWORK_PAIRED_CASES={checks}/{checks} PASS")
    print(f"ALPHA4_NETWORK_ACCEPTED_PROJECTIONS={accepted} UNKNOWN/EFFECT_FALSE")
    print(f"ALPHA4_NETWORK_FIELD_SENSITIVITY={sensitivity}/{sensitivity} PASS")
    print("ALPHA4_NETWORK_PAIRED_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
