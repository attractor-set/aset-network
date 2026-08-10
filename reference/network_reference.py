from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def empty_state() -> dict[str, Any]:
    return {"imports": {}, "history": []}


def _result(accepted: bool, code: str, state_changed: bool) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": state_changed,
        "semantic_status": "UNKNOWN" if code != "UNKNOWN_TRANSITION" else "NOT_APPLICABLE",
        "enforcement": "BLOCKED" if code != "UNKNOWN_TRANSITION" else "NOT_APPLICABLE",
    }


def apply_transition(
    state: dict[str, Any] | None,
    transition: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if state is None:
        state = empty_state()
    state = copy.deepcopy(state)
    if transition.get("kind") != "ADMIT_IMPORT":
        return state, _result(False, "UNKNOWN_TRANSITION", False)

    observation = copy.deepcopy(transition["payload"]["import"])
    iid = observation["import_id"]
    existing = state["imports"].get(iid)
    if existing == observation:
        return state, _result(True, "IDEMPOTENT_REPLAY", False)
    if existing is not None:
        return state, _result(False, "IDENTIFIER_CONFLICT", False)
    if observation["semantic_status"] != "UNKNOWN" or observation["enforcement"] != "BLOCKED":
        return state, _result(False, "IMPORT_MUST_START_BLOCKED", False)

    state["imports"][iid] = observation
    result = _result(True, "IMPORT_ADMITTED", True)
    state["history"].append(_digest({"transition": transition, "result": result}))
    return state, result


def execute_case(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    state = copy.deepcopy(case["initial_state"])
    result = _result(False, "NO_STEPS", False)
    for transition in case["steps"]:
        state, result = apply_transition(state, transition)
        if not result["accepted"]:
            break
    return state, result
