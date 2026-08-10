from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def empty_state() -> None:
    return None


def _result(
    accepted: bool,
    code: str,
    changed: bool,
    status: str = "NOT_APPLICABLE",
    enforcement: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "semantic_status": status,
        "enforcement": enforcement,
    }


def apply_transition(
    state: dict[str, Any] | None,
    transition: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    before = copy.deepcopy(state)
    kind = transition["kind"]
    payload = transition["payload"]

    if kind == "FEDERATION_GENESIS":
        if state is not None:
            return state, _result(False, "FEDERATION_ALREADY_EXISTS", False)
        state = {
            "federation_id": payload["federation_id"],
            "federation_epoch": payload.get("federation_epoch", 0),
            "constitution_digest": payload["constitution_digest"],
            "members": {},
            "routes": {},
            "exports": {},
            "imports": {},
            "recognitions": {},
            "history": [],
        }
        return _append(state, transition, _result(True, "FEDERATION_CREATED", True))

    if state is None:
        return state, _result(False, "FEDERATION_NOT_FOUND", False)

    state = copy.deepcopy(state)

    if kind == "MEMBER_JOIN":
        member = payload["member"]
        cid = member["context_id"]
        existing = state["members"].get(cid)
        if existing == member:
            return state, _result(True, "IDEMPOTENT_REPLAY", False)
        if existing is not None:
            return state, _result(False, "IDENTIFIER_CONFLICT", False)
        if member["status"] != "ACTIVE":
            return state, _result(False, "MEMBER_NOT_ACTIVE", False)
        state["members"][cid] = copy.deepcopy(member)
        return _append(state, transition, _result(True, "MEMBER_JOINED", True))

    if kind == "ROUTE_GRANT":
        route = payload["route"]
        rid = route["route_id"]
        existing = state["routes"].get(rid)
        if existing == route:
            return state, _result(True, "IDEMPOTENT_REPLAY", False)
        if existing is not None:
            return state, _result(False, "IDENTIFIER_CONFLICT", False)
        source = state["members"].get(route["source_context_id"])
        target = state["members"].get(route["target_context_id"])
        if source is None or target is None:
            return state, _result(False, "ROUTE_MEMBER_UNKNOWN", False)
        if source["status"] != "ACTIVE" or target["status"] != "ACTIVE":
            return state, _result(False, "ROUTE_MEMBER_INACTIVE", False)
        if route["source_context_id"] == route["target_context_id"]:
            return state, _result(False, "SELF_ROUTE_FORBIDDEN", False)
        if (
            route["source_policy_epoch"] != source["policy_epoch"]
            or route["target_policy_epoch"] != target["policy_epoch"]
        ):
            return state, _result(False, "POLICY_EPOCH_MISMATCH", False)
        if route["status"] != "ACTIVE":
            return state, _result(False, "ROUTE_NOT_ACTIVE", False)
        state["routes"][rid] = copy.deepcopy(route)
        return _append(state, transition, _result(True, "ROUTE_GRANTED", True))

    if kind == "EXPORT_ARTIFACT":
        export = payload["export"]
        eid = export["export_id"]
        existing = state["exports"].get(eid)
        if existing == export:
            return state, _result(True, "IDEMPOTENT_REPLAY", False)
        if existing is not None:
            return state, _result(False, "IDENTIFIER_CONFLICT", False)
        route = state["routes"].get(export["route_id"])
        if route is None:
            return state, _result(False, "ROUTE_NOT_FOUND", False)
        if route["status"] != "ACTIVE":
            return state, _result(False, "ROUTE_SUSPENDED", False)
        exact = (
            export["source_context_id"] == route["source_context_id"]
            and export["target_context_id"] == route["target_context_id"]
            and export["scope_digest"] == route["scope_digest"]
            and export["source_policy_epoch"] == route["source_policy_epoch"]
        )
        if not exact:
            return state, _result(False, "ROUTE_BINDING_MISMATCH", False)
        state["exports"][eid] = copy.deepcopy(export)
        return _append(
            state,
            transition,
            _result(
                True,
                "ARTIFACT_EXPORTED",
                True,
                "NOT_APPLICABLE",
                "NOT_APPLICABLE",
            ),
        )

    if kind == "OBSERVE_IMPORT":
        observation = payload["import"]
        iid = observation["import_id"]
        existing = state["imports"].get(iid)
        if existing == observation:
            return state, _result(True, "IDEMPOTENT_REPLAY", False, "UNKNOWN", "BLOCKED")
        if existing is not None:
            return state, _result(False, "IDENTIFIER_CONFLICT", False, "UNKNOWN", "BLOCKED")
        export = state["exports"].get(observation["export_id"])
        route = state["routes"].get(observation["route_id"])
        if export is None or route is None:
            return state, _result(False, "EXPORT_OR_ROUTE_NOT_FOUND", False, "UNKNOWN", "BLOCKED")
        target = state["members"].get(observation["target_context_id"])
        if target is None or target["status"] != "ACTIVE":
            return state, _result(False, "TARGET_CONTEXT_INACTIVE", False, "UNKNOWN", "BLOCKED")
        exact = (
            observation["route_id"] == export["route_id"]
            and (
                observation["target_context_id"]
                == export["target_context_id"]
                == route["target_context_id"]
            )
            and observation["artifact_digest"] == export["artifact_digest"]
            and observation["scope_digest"] == export["scope_digest"] == route["scope_digest"]
            and (
                observation["target_policy_epoch"]
                == route["target_policy_epoch"]
                == target["policy_epoch"]
            )
        )
        if not exact:
            return state, _result(False, "IMPORT_BINDING_MISMATCH", False, "UNKNOWN", "BLOCKED")
        if observation["semantic_status"] != "UNKNOWN" or observation["enforcement"] != "BLOCKED":
            return state, _result(False, "IMPORT_MUST_START_BLOCKED", False, "UNKNOWN", "BLOCKED")
        state["imports"][iid] = copy.deepcopy(observation)
        return _append(
            state,
            transition,
            _result(True, "IMPORT_OBSERVED", True, "UNKNOWN", "BLOCKED"),
        )

    if kind == "RECORD_RECOGNITION":
        receipt = payload["recognition"]
        rid = receipt["recognition_id"]
        existing = state["recognitions"].get(rid)
        if existing == receipt:
            return state, _result(
                True,
                "IDEMPOTENT_REPLAY",
                False,
                receipt["semantic_status"],
                receipt["enforcement"],
            )
        if existing is not None:
            return state, _result(False, "IDENTIFIER_CONFLICT", False, "UNKNOWN", "BLOCKED")
        observation = state["imports"].get(receipt["import_id"])
        if observation is None:
            return state, _result(False, "IMPORT_NOT_FOUND", False, "UNKNOWN", "BLOCKED")
        exact = all(
            receipt[k] == observation[k]
            for k in (
                "target_context_id",
                "resolution_id",
                "question_digest",
                "scope_digest",
                "target_policy_epoch",
            )
        )
        if not exact:
            return state, _result(False, "SEED_BINDING_MISMATCH", False, "UNKNOWN", "BLOCKED")
        status = receipt["semantic_status"]
        enforcement = receipt["enforcement"]
        if status not in {"ACCEPT", "DENY"}:
            return state, _result(
                False,
                "TERMINAL_SEED_DECISION_REQUIRED",
                False,
                "UNKNOWN",
                "BLOCKED",
            )
        if (status, enforcement) not in {("ACCEPT", "ALLOW"), ("DENY", "BLOCKED")}:
            return state, _result(False, "SEED_ENFORCEMENT_MISMATCH", False, "UNKNOWN", "BLOCKED")
        state["recognitions"][rid] = copy.deepcopy(receipt)
        code = "LOCALLY_RECOGNIZED" if status == "ACCEPT" else "LOCALLY_REJECTED"
        return _append(state, transition, _result(True, code, True, status, enforcement))

    if kind == "SUSPEND_ROUTE":
        rid = payload["route_id"]
        route = state["routes"].get(rid)
        if route is None:
            return state, _result(False, "ROUTE_NOT_FOUND", False)
        if route["status"] == "SUSPENDED":
            return state, _result(True, "IDEMPOTENT_REPLAY", False)
        route["status"] = "SUSPENDED"
        return _append(state, transition, _result(True, "ROUTE_SUSPENDED", True))

    if kind == "MEMBER_WITHDRAW":
        cid = payload["context_id"]
        member = state["members"].get(cid)
        if member is None:
            return state, _result(False, "MEMBER_NOT_FOUND", False)
        if member["status"] == "WITHDRAWN":
            return state, _result(True, "IDEMPOTENT_REPLAY", False)
        active_routes = [
            r
            for r in state["routes"].values()
            if r["status"] == "ACTIVE" and cid in {r["source_context_id"], r["target_context_id"]}
        ]
        if active_routes:
            return state, _result(False, "ACTIVE_ROUTE_DEPENDENCY", False)
        member["status"] = "WITHDRAWN"
        return _append(state, transition, _result(True, "MEMBER_WITHDRAWN", True))

    return before, _result(False, "UNKNOWN_TRANSITION", False)


def _append(
    state: dict[str, Any],
    transition: dict[str, Any],
    result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    state["history"].append(_digest({"transition": transition, "result": result}))
    return state, result


def execute_case(case: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    state = copy.deepcopy(case["initial_state"])
    result = _result(False, "NO_STEPS", False)
    for transition in case["steps"]:
        state, result = apply_transition(state, transition)
        if not result["accepted"]:
            break
    return state, result
