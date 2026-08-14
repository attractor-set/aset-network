from __future__ import annotations

import argparse
import itertools
import json
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.alpha4_network_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]


class NetworkExpressionAirgapError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NetworkExpressionAirgapError(message)


def execute(path: Path) -> dict[str, Any]:
    namespace: dict[str, Any] = {"__file__": str(path)}
    source = path.read_text(encoding="utf-8")
    exec(compile(source, str(path), "exec"), namespace)
    return namespace


def _powerset(values: set[str]) -> list[set[str]]:
    ordered = sorted(values)
    return [
        {item for item, included in zip(ordered, mask, strict=True) if included}
        for mask in itertools.product((False, True), repeat=len(ordered))
    ]


def _core_expected(
    imports: list[dict[str, Any]], observation: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    identical = observation in imports
    identifier_exists = any(item["import_id"] == observation["import_id"] for item in imports)
    if identical:
        return [dict(item) for item in imports], {
            "accepted": True,
            "code": "IDEMPOTENT_REPLAY",
            "state_changed": False,
        }
    if identifier_exists:
        return [dict(item) for item in imports], {
            "accepted": False,
            "code": "IDENTIFIER_CONFLICT",
            "state_changed": False,
        }
    return [*[dict(item) for item in imports], dict(observation)], {
        "accepted": True,
        "code": "IMPORT_ADMITTED",
        "state_changed": True,
    }


def _check_core(network: dict[str, Any], seed: dict[str, Any]) -> int:
    admit = network.get("admit_import")
    make_seed_state = seed.get("state")
    seed_apply = seed.get("apply_component")
    require(
        callable(admit) and callable(make_seed_state) and callable(seed_apply),
        "Python companion entry points missing",
    )
    digests = ["sha256:" + ch * 64 for ch in ("0", "1")]
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
    states.extend([[dict(item)] for item in observations])
    cases = 0
    for imports in states:
        for observation in observations:
            seed_before = make_seed_state("subject-1", "authority-1")
            actual_imports, actual_seed, actual_result = admit(imports, observation, seed_before)
            expected_imports, expected_result = _core_expected(imports, observation)
            require(actual_imports == expected_imports, "generated Python Network state mismatch")
            for key, value in expected_result.items():
                require(actual_result.get(key) == value, f"generated Python result mismatch: {key}")
            if expected_result["accepted"]:
                expected_seed = seed_apply(
                    seed_before,
                    "ASET-COMPONENT-OBSERVE-UNKNOWN",
                    evidence=observation["evidence_digest"],
                )
                require(
                    actual_seed == expected_seed,
                    "generated Python does not extend exact Seed OBSERVE-UNKNOWN",
                )
                require(
                    actual_result["seed_projection"]
                    == {
                        "component": "ASET-COMPONENT-OBSERVE-UNKNOWN",
                        "recognition": "UNKNOWN",
                        "effect_permitted": False,
                    },
                    "accepted Python projection crossed Seed boundary",
                )
            else:
                require(actual_seed == seed_before, "rejected Network import changed Seed state")
            cases += 1
    return cases


def _check_dynamic(network: dict[str, Any]) -> int:
    applicable = network.get("profile_applicable")
    stutter = network.get("profile_network_stutter")
    require(callable(applicable) and callable(stutter), "dynamic Python expressions missing")
    cases = 0
    for exact, recognition in itertools.product((False, True), ("UNKNOWN", "ALLOW", "BLOCK")):
        require(
            applicable(exact, recognition) == (exact and recognition == "ALLOW"),
            "dynamic applicability mismatch",
        )
        cases += 1
    for before, after in itertools.product(("n0", "n1"), repeat=2):
        require(stutter(before, after) == (before == after), "dynamic stutter mismatch")
        cases += 1
    return cases


def _check_liveness(network: dict[str, Any]) -> int:
    assumptions_all = {
        "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
        "EVENTUAL_TARGET_OBSERVATION",
        "TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION",
        "NO_PERMANENT_TARGET_UNAVAILABILITY",
    }
    delivered = network.get("eventually_delivered_claim")
    observed = network.get("eventually_observed_claim")
    resolved = network.get("eventually_resolved_claim")
    permitted = network.get("resolved_result_permitted")
    require(
        all(callable(item) for item in (delivered, observed, resolved, permitted)),
        "liveness Python expressions missing",
    )
    cases = 0
    for assumptions in _powerset(assumptions_all):
        expected_delivery = {
            "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
            "NO_PERMANENT_TARGET_UNAVAILABILITY",
        } <= assumptions
        require(delivered(assumptions) == expected_delivery, "liveness delivery mismatch")
        expected_observation = {
            "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
            "EVENTUAL_TARGET_OBSERVATION",
            "NO_PERMANENT_TARGET_UNAVAILABILITY",
        } <= assumptions
        require(observed(assumptions) == expected_observation, "liveness observation mismatch")
        require(
            resolved(assumptions) == (assumptions_all <= assumptions),
            "liveness resolution mismatch",
        )
        cases += 3
    for result in ("UNKNOWN", "ALLOW", "BLOCK"):
        require(permitted(result) == (result in {"ALLOW", "BLOCK"}), "liveness result mismatch")
        cases += 1
    return cases


def _check_composition(network: dict[str, Any]) -> int:
    required = {"RETAINED_EXPORT", "DELIVERY", "TARGET_OBSERVATION"}
    capabilities = network.get("required_capabilities_satisfied")
    boundary = network.get("composition_boundary_preserved")
    delivery = network.get("delivery_witness")
    observation = network.get("observation_witness")
    resolution = network.get("resolution_witness")
    progress = network.get("progress_witness")
    require(
        all(
            callable(item)
            for item in (capabilities, boundary, delivery, observation, resolution, progress)
        ),
        "composition Python expressions missing",
    )
    cases = 0
    for provided in _powerset(required):
        require(capabilities(provided) == (required <= provided), "composition capability mismatch")
        cases += 1
    for values in itertools.product((False, True), repeat=4):
        require(boundary(*values) == (not any(values)), "composition boundary mismatch")
        cases += 1
    export = "e0"
    sets = (set(), {export})
    for exported, delivered_set, observed_set, resolved_set in itertools.product(sets, repeat=4):
        expected = (
            export in exported and export in delivered_set,
            export in delivered_set and export in observed_set,
            export in observed_set and export in resolved_set,
        )
        actual = (
            delivery(exported, delivered_set, export),
            observation(delivered_set, observed_set, export),
            resolution(observed_set, resolved_set, export),
        )
        require(actual == expected, "composition witness mismatch")
        require(
            progress(exported, delivered_set, observed_set, resolved_set, export) == all(expected),
            "composition progress mismatch",
        )
        cases += 4
    return cases


FedState = tuple[bool, int, int, int, bool]


def _expected_federation_edges(state: FedState) -> set[tuple[str, str, FedState]]:
    created, a, b, route, exported = state
    out: set[tuple[str, str, FedState]] = set()
    if not created:
        out.add(("ASET-NETWORK-FEDERATION-GENESIS", "-", (True, a, b, route, exported)))
    if created and a == 0:
        out.add(("ASET-NETWORK-MEMBER-JOIN", "A", (created, 1, b, route, exported)))
    if created and b == 0:
        out.add(("ASET-NETWORK-MEMBER-JOIN", "B", (created, a, 1, route, exported)))
    if created and a == 1 and b == 1 and route == 0:
        out.add(("ASET-NETWORK-ROUTE-GRANT", "A-B", (created, a, b, 1, exported)))
    if route == 1 and not exported:
        out.add(("ASET-NETWORK-EXPORT-ARTIFACT", "A-B", (created, a, b, route, True)))
    if route == 1:
        out.add(("ASET-NETWORK-SUSPEND-ROUTE", "A-B", (created, a, b, 2, exported)))
    if a == 1 and route != 1:
        out.add(("ASET-NETWORK-MEMBER-WITHDRAW", "A", (created, 2, b, route, exported)))
    if b == 1 and route != 1:
        out.add(("ASET-NETWORK-MEMBER-WITHDRAW", "B", (created, a, 2, route, exported)))
    return out


def _to_generated_state(network: dict[str, Any], state: FedState) -> dict[str, Any]:
    created, a, b, route, exported = state
    value = network["federation_state"]()
    if created:
        value["federation_id"] = "f0"
        value["federation_epoch"] = "e0"
    member_map = {0: "ABSENT", 1: "ACTIVE", 2: "WITHDRAWN"}
    if a:
        value["members"]["A"] = member_map[a]
    if b:
        value["members"]["B"] = member_map[b]
    route_map = {0: "ABSENT", 1: "ACTIVE", 2: "SUSPENDED"}
    if route:
        value["routes"][("A", "B")] = route_map[route]
    if exported:
        value["exports"] = frozenset({("A", "B", "x0")})
    return value


def _from_generated_state(value: dict[str, Any]) -> FedState:
    member_map = {"ABSENT": 0, "ACTIVE": 1, "WITHDRAWN": 2}
    route_map = {"ABSENT": 0, "ACTIVE": 1, "SUSPENDED": 2}
    return (
        value["federation_id"] is not None,
        member_map[value["members"].get("A", "ABSENT")],
        member_map[value["members"].get("B", "ABSENT")],
        route_map[value["routes"].get(("A", "B"), "ABSENT")],
        ("A", "B", "x0") in value["exports"],
    )


def _actual_federation_edges(
    network: dict[str, Any], state: FedState
) -> set[tuple[str, str, FedState]]:
    current = _to_generated_state(network, state)
    candidates: tuple[tuple[str, str, Callable[[], dict[str, Any]]], ...] = (
        (
            "ASET-NETWORK-FEDERATION-GENESIS",
            "-",
            lambda: network["federation_genesis"](current, "f0", "e0"),
        ),
        ("ASET-NETWORK-MEMBER-JOIN", "A", lambda: network["member_join"](current, "A")),
        ("ASET-NETWORK-MEMBER-JOIN", "B", lambda: network["member_join"](current, "B")),
        ("ASET-NETWORK-ROUTE-GRANT", "A-B", lambda: network["route_grant"](current, "A", "B")),
        (
            "ASET-NETWORK-EXPORT-ARTIFACT",
            "A-B",
            lambda: network["export_artifact"](current, "A", "B", "x0"),
        ),
        ("ASET-NETWORK-SUSPEND-ROUTE", "A-B", lambda: network["suspend_route"](current, "A", "B")),
        ("ASET-NETWORK-MEMBER-WITHDRAW", "A", lambda: network["member_withdraw"](current, "A")),
        ("ASET-NETWORK-MEMBER-WITHDRAW", "B", lambda: network["member_withdraw"](current, "B")),
    )
    out: set[tuple[str, str, FedState]] = set()
    for component, actor, call in candidates:
        try:
            target = call()
        except ValueError:
            continue
        out.add((component, actor, _from_generated_state(target)))
    return out


def _check_federation(network: dict[str, Any]) -> tuple[int, int]:
    required = (
        "federation_state",
        "federation_genesis",
        "member_join",
        "route_grant",
        "export_artifact",
        "suspend_route",
        "member_withdraw",
    )
    require(
        all(callable(network.get(name)) for name in required),
        "federation Python expressions missing",
    )
    initial: FedState = (False, 0, 0, 0, False)
    queue = deque([initial])
    seen = {initial}
    edges = 0
    while queue:
        state = queue.popleft()
        expected = _expected_federation_edges(state)
        actual = _actual_federation_edges(network, state)
        require(actual == expected, f"federation Python edge mismatch: {state!r}")
        edges += len(expected)
        for _, _, target in expected:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    require(len(seen) == 20 and edges == 25, "federation air-gap state-space drift")
    return len(seen), edges


def check_airgap(profiles_root: Path) -> dict[str, Any]:
    binding = parse_seed_binding()
    profiles_root = profiles_root.resolve()
    before = tree_digest(profiles_root)
    network_path = profiles_root / "python/aset_network_alpha4.py"
    seed_path = profiles_root / "base/seed/python/aset_seed_alpha4.py"
    require(network_path.is_file(), "Network Python companion missing")
    require(seed_path.is_file(), "exact Seed Python base missing")
    require(sha256(seed_path) == binding.companions["PYTHON"][1], "Seed Python base bytes mismatch")
    seed = execute(seed_path)
    network = execute(network_path)
    require(
        network.get("BASE_SEED_EXPRESSION_SHA256") == sha256(seed_path),
        "Network Python base binding mismatch",
    )
    core = _check_core(network, seed)
    dynamic = _check_dynamic(network)
    federation_states, federation_edges = _check_federation(network)
    liveness = _check_liveness(network)
    composition = _check_composition(network)
    total = core + dynamic + federation_edges + liveness + composition
    require(
        (core, dynamic, federation_states, federation_edges, liveness, composition, total)
        == (272, 10, 20, 25, 51, 88, 446),
        "Network Python air-gap coverage drift",
    )
    after = tree_digest(profiles_root)
    require(after == before, "Network profile tree changed during air-gap verification")
    return {
        "document_type": "aset-network-python-companion-airgap-evidence",
        "semantic_precedence": "NONE",
        "base_relation": "EXTENSION_OF_EXACT_SEED_PYTHON_EXPRESSION",
        "assurance_dependencies": {
            "network_semantic_source": "NONE",
            "release_profile_generator": "NONE",
            "triangulated_expression_checker": "NONE",
        },
        "profile_tree_digest": before,
        "inputs": {
            "seed_python": {
                "path": "base/seed/python/aset_seed_alpha4.py",
                "sha256": sha256(seed_path),
            },
            "network_python": {
                "path": "python/aset_network_alpha4.py",
                "sha256": sha256(network_path),
            },
        },
        "coverage": {
            "core_cases": core,
            "dynamic_cases": dynamic,
            "federation_states": federation_states,
            "federation_edges": federation_edges,
            "liveness_cases": liveness,
            "composition_cases": composition,
            "total_cases": total,
        },
        "profile_tree_unchanged": True,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/network-python-airgap-evidence.json",
    )
    args = parser.parse_args()
    try:
        evidence = check_airgap(args.profiles_root)
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        coverage = evidence["coverage"]
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_CORE={coverage['core_cases']}/272 PASS")
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_DYNAMIC={coverage['dynamic_cases']}/10 PASS")
        print(
            "ALPHA4_NETWORK_PYTHON_AIRGAP_FEDERATION="
            f"STATES:{coverage['federation_states']} "
            f"EDGES:{coverage['federation_edges']} PASS"
        )
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_LIVENESS={coverage['liveness_cases']}/51 PASS")
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_COMPOSITION={coverage['composition_cases']}/88 PASS")
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_TOTAL={coverage['total_cases']}/446 PASS")
        print("ALPHA4_NETWORK_PYTHON_SEED_BASE=EXACT")
        print("ALPHA4_NETWORK_PYTHON_SEMANTIC_SOURCE_DEPENDENCY=NONE")
        print("ALPHA4_NETWORK_PYTHON_GENERATOR_DEPENDENCY=NONE")
        print("ALPHA4_NETWORK_PYTHON_PROFILE_TREE_UNCHANGED=PASS")
        print("ALPHA4_NETWORK_PYTHON_AIRGAP=PASS")
        return 0
    except (KeyError, OSError, TypeError, ValueError, NetworkExpressionAirgapError) as error:
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_ERROR={error}")
        print("ALPHA4_NETWORK_PYTHON_AIRGAP=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
