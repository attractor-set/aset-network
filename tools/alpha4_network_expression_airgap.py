from __future__ import annotations

import argparse
import ast
import builtins
import io
import itertools
import json
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.alpha4_network_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]


_ALLOWED_DIRECT_IMPORTS = frozenset({"hashlib"})
_ALLOWED_FROM_IMPORTS = {
    "pathlib": frozenset({"Path"}),
    "typing": frozenset({"Any"}),
}
_FILESYSTEM_INSPECTION_METHODS = frozenset(
    {
        "absolute",
        "cwd",
        "exists",
        "expanduser",
        "glob",
        "group",
        "home",
        "is_block_device",
        "is_char_device",
        "is_dir",
        "is_fifo",
        "is_file",
        "is_mount",
        "is_socket",
        "is_symlink",
        "iterdir",
        "lstat",
        "owner",
        "readlink",
        "resolve",
        "rglob",
        "samefile",
        "stat",
        "walk",
    }
)

_FILESYSTEM_MUTATION_METHODS = frozenset(
    {
        "write_text",
        "write_bytes",
        "unlink",
        "rename",
        "replace",
        "mkdir",
        "touch",
        "chmod",
        "symlink_to",
        "hardlink_to",
    }
)

_DENIED_RUNTIME_BUILTINS = frozenset(
    {
        "breakpoint",
        "copyright",
        "credits",
        "delattr",
        "dir",
        "eval",
        "exit",
        "getattr",
        "globals",
        "help",
        "input",
        "license",
        "locals",
        "quit",
        "setattr",
        "type",
        "vars",
    }
)


class NetworkExpressionAirgapError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NetworkExpressionAirgapError(message)


def _validate_companion_ast(
    source: str, *, allowed_imports: frozenset[str], allow_seed_loader: bool
) -> None:
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    def enclosing_function(node: ast.AST) -> str | None:
        current = node
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                require(
                    alias.asname is None
                    and alias.name in allowed_imports
                    and alias.name in _ALLOWED_DIRECT_IMPORTS,
                    f"air-gap companion import forbidden: {alias.name}",
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported = {alias.name for alias in node.names}
            require(node.level == 0, "air-gap companion relative import forbidden")
            if module == "__future__":
                require(
                    imported == {"annotations"}
                    and all(alias.asname is None for alias in node.names),
                    "air-gap companion future import drift",
                )
            else:
                require(
                    module in allowed_imports
                    and module in _ALLOWED_FROM_IMPORTS
                    and imported <= _ALLOWED_FROM_IMPORTS[module]
                    and all(alias.asname is None for alias in node.names),
                    f"air-gap companion import forbidden: {module}",
                )
        elif isinstance(node, ast.Name) and node.id == "__builtins__":
            raise NetworkExpressionAirgapError("air-gap companion accesses __builtins__")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise NetworkExpressionAirgapError(
                    f"air-gap companion private attribute forbidden: {node.attr}"
                )
            require(
                node.attr not in _FILESYSTEM_INSPECTION_METHODS,
                f"air-gap companion filesystem inspection forbidden: {node.attr}",
            )
            require(
                node.attr not in _FILESYSTEM_MUTATION_METHODS,
                f"air-gap companion filesystem mutation forbidden: {node.attr}",
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {
                "__import__",
                "breakpoint",
                "delattr",
                "dir",
                "eval",
                "getattr",
                "globals",
                "help",
                "input",
                "locals",
                "setattr",
                "type",
                "vars",
            }:
                raise NetworkExpressionAirgapError(
                    f"air-gap companion dynamic capability forbidden: {node.func.id}"
                )
            if node.func.id in {"exec", "compile"}:
                require(
                    allow_seed_loader and enclosing_function(node) == "_load_seed_base",
                    f"air-gap companion {node.func.id} permitted only for exact Seed base loader",
                )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            require(
                node.func.attr not in _FILESYSTEM_INSPECTION_METHODS,
                f"air-gap companion filesystem inspection forbidden: {node.func.attr}",
            )
            require(
                node.func.attr
                not in {
                    "write_text",
                    "write_bytes",
                    "unlink",
                    "rename",
                    "replace",
                    "mkdir",
                    "touch",
                    "chmod",
                    "symlink_to",
                    "hardlink_to",
                },
                f"air-gap companion filesystem mutation forbidden: {node.func.attr}",
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            require(
                not any(
                    marker in lowered for marker in ("tools.", "tools/", ".tla", ".forth", ".petri")
                ),
                "air-gap companion embeds repository semantic-source locator",
            )


def execute(
    path: Path,
    allowed_root: Path,
    *,
    allowed_imports: frozenset[str],
    allow_seed_loader: bool,
) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    _validate_companion_ast(
        source, allowed_imports=allowed_imports, allow_seed_loader=allow_seed_loader
    )
    allowed_root = allowed_root.resolve()
    original_io_open = io.open

    def guarded_open(file: object, *args: object, **kwargs: object):
        if isinstance(file, int):
            return original_io_open(file, *args, **kwargs)
        mode = kwargs.get("mode", args[0] if args else "r")
        require(
            isinstance(mode, str) and not any(flag in mode for flag in "wax+"),
            "air-gap companion file access must be read-only",
        )
        candidate = Path(file).resolve()  # type: ignore[arg-type]
        require(
            candidate == allowed_root or allowed_root in candidate.parents,
            f"air-gap companion file access escaped materialized profile tree: {candidate}",
        )
        return original_io_open(file, *args, **kwargs)

    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        requested = set(fromlist or ())
        if level != 0:
            raise ImportError("air-gap companion relative import forbidden")
        if name == "__future__":
            if requested != {"annotations"}:
                raise ImportError("air-gap companion future import drift")
        elif name in _ALLOWED_DIRECT_IMPORTS:
            if name not in allowed_imports or requested:
                raise ImportError(f"air-gap companion import forbidden: {name}")
        elif name in _ALLOWED_FROM_IMPORTS:
            if (
                name not in allowed_imports
                or not requested
                or not requested <= _ALLOWED_FROM_IMPORTS[name]
            ):
                raise ImportError(f"air-gap companion import forbidden: {name}")
        else:
            raise ImportError(f"air-gap companion import forbidden: {name}")
        return original_import(name, globals, locals, fromlist, level)

    original_compile = builtins.compile
    original_exec = builtins.exec
    approved_exec_codes: dict[int, object] = {}
    expected_seed_base = (
        allowed_root / "base" / "seed" / "python" / "aset_seed_alpha4.py"
    ).resolve()

    def denied(*args: object, **kwargs: object) -> object:
        raise NetworkExpressionAirgapError(
            "air-gap companion attempted forbidden runtime capability"
        )

    def guarded_compile(
        source_value: object,
        filename: object,
        mode: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        require(
            allow_seed_loader,
            "air-gap companion compile forbidden outside exact Seed base loader",
        )
        require(
            isinstance(source_value, (str, bytes)) and isinstance(filename, str) and mode == "exec",
            "air-gap companion compile permitted only for exact Seed base loader",
        )
        candidate = Path(filename).resolve()
        require(
            candidate == expected_seed_base,
            "air-gap companion compile path is not exact Seed base",
        )
        with original_io_open(candidate, "rb") as stream:
            expected_bytes = stream.read()
        actual_bytes = (
            source_value.encode("utf-8") if isinstance(source_value, str) else source_value
        )
        require(
            actual_bytes == expected_bytes,
            "air-gap companion compiled Seed source bytes mismatch",
        )
        code = original_compile(
            source_value,
            filename,
            mode,
            *args,
            **kwargs,
        )
        approved_exec_codes[id(code)] = code
        return code

    safe_builtins = dict(vars(builtins))
    for name in _DENIED_RUNTIME_BUILTINS:
        if name in safe_builtins:
            safe_builtins[name] = denied
    safe_builtins["__import__"] = guarded_import
    safe_builtins["open"] = guarded_open
    safe_builtins["compile"] = guarded_compile

    def guarded_exec(
        code: object,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
    ) -> None:
        require(
            allow_seed_loader and approved_exec_codes.get(id(code)) is code,
            "air-gap companion exec permitted only for exact Seed base code",
        )
        approved_exec_codes.pop(id(code), None)
        target_globals = {} if globals_dict is None else globals_dict
        target_globals["__builtins__"] = safe_builtins
        original_exec(code, target_globals, locals_dict)

    safe_builtins["exec"] = guarded_exec
    namespace: dict[str, Any] = {
        "__file__": str(path),
        "__name__": "aset_network_alpha4_airgap_subject",
        "__builtins__": safe_builtins,
    }
    io.open = guarded_open  # type: ignore[assignment]
    try:
        exec(compile(source, str(path), "exec"), namespace)
    finally:
        io.open = original_io_open  # type: ignore[assignment]
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


def _check_core_identity_sensitivity(network: dict[str, Any], seed: dict[str, Any]) -> int:
    admit = network["admit_import"]
    make_seed_state = seed["state"]
    base = {
        "import_id": "i0",
        "source_context": "s0",
        "target_context": "t0",
        "evidence_digest": "sha256:" + "0" * 64,
    }
    replacements = {
        "import_id": "i1",
        "source_context": "s1",
        "target_context": "t1",
        "evidence_digest": "sha256:" + "1" * 64,
    }
    checks = 0
    for field, replacement in replacements.items():
        candidate = {**base, field: replacement}
        state = [dict(base)]
        seed_before = make_seed_state("subject-1", "authority-1")
        actual_state, _, actual_result = admit(state, candidate, seed_before)
        expected_state, expected_result = _core_expected(state, candidate)
        require(
            actual_state == expected_state,
            f"core identity sensitivity state mismatch: {field}",
        )
        for key, value in expected_result.items():
            require(
                actual_result.get(key) == value,
                f"core identity sensitivity result mismatch: {field}:{key}",
            )
        checks += 1

    first = {**base, "import_id": "i1"}
    state = [first, dict(base)]
    seed_before = make_seed_state("subject-1", "authority-1")
    actual_state, _, actual_result = admit(state, dict(base), seed_before)
    require(actual_state == state, "core second-position replay changed state")
    require(actual_result.get("code") == "IDEMPOTENT_REPLAY", "core second-position replay missed")
    return checks + 1


def _check_composition_identity_sensitivity(network: dict[str, Any]) -> int:
    delivery = network["delivery_witness"]
    export = "e0"
    sets = (set(), {"e0"}, {"e1"}, {"e0", "e1"})
    checks = 0
    for exported, delivered in itertools.product(sets, repeat=2):
        require(
            delivery(exported, delivered, export) == (export in exported and export in delivered),
            "composition foreign-export identity sensitivity mismatch",
        )
        checks += 1
    return checks


def _check_federation_identity_sensitivity(network: dict[str, Any]) -> int:
    checks = 0
    empty = network["federation_state"]()
    created = network["federation_genesis"](empty, "f1", "e1")
    require(created["federation_id"] == "f1", "federation id identity lost")
    checks += 1
    require(created["federation_epoch"] == "e1", "federation epoch identity lost")
    checks += 1
    joined = network["member_join"](created, "B")
    require(
        joined["members"].get("B") == "ACTIVE" and "A" not in joined["members"],
        "member identity lost",
    )
    checks += 1
    joined_a = network["member_join"](joined, "A")
    granted = network["route_grant"](joined_a, "B", "A")
    require(granted["routes"].get(("B", "A")) == "ACTIVE", "route endpoint identity lost")
    checks += 1
    exported = network["export_artifact"](granted, "B", "A", "x1")
    require(("B", "A", "x1") in exported["exports"], "artifact identity lost")
    checks += 1
    return checks


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
    seed = execute(seed_path, profiles_root, allowed_imports=frozenset(), allow_seed_loader=False)
    network = execute(
        network_path,
        profiles_root,
        allowed_imports=frozenset({"hashlib", "pathlib", "typing"}),
        allow_seed_loader=True,
    )
    require(
        network.get("BASE_SEED_EXPRESSION_SHA256") == sha256(seed_path),
        "Network Python base binding mismatch",
    )
    core = _check_core(network, seed)
    dynamic = _check_dynamic(network)
    federation_states, federation_edges = _check_federation(network)
    liveness = _check_liveness(network)
    composition = _check_composition(network)
    core_identity = _check_core_identity_sensitivity(network, seed)
    composition_identity = _check_composition_identity_sensitivity(network)
    federation_identity = _check_federation_identity_sensitivity(network)
    total = core + dynamic + federation_edges + liveness + composition
    sensitivity = core_identity + composition_identity + federation_identity
    require(
        (core, dynamic, federation_states, federation_edges, liveness, composition, total)
        == (272, 10, 20, 25, 51, 88, 446),
        "Network Python air-gap structural coverage drift",
    )
    require(
        (core_identity, composition_identity, federation_identity, sensitivity) == (5, 16, 5, 26),
        "Network Python air-gap identity sensitivity drift",
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
            "companion_import_surface": "RESTRICTED",
            "companion_file_access": "MATERIALIZED_PROFILE_TREE_READ_ONLY",
            "companion_dynamic_builtins": "DENIED",
            "companion_filesystem_method_aliasing": "DENIED",
            "companion_seed_loader_exec": "EXACT_SEED_BASE_BYTES_ONLY",
            "runtime_capability_isolation": "PASS",
            "process_isolation": "NOT_CLAIMED",
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
            "core_identity_sensitivity_cases": core_identity,
            "composition_identity_sensitivity_cases": composition_identity,
            "federation_identity_sensitivity_cases": federation_identity,
            "sensitivity_cases": sensitivity,
            "grand_total_cases": total + sensitivity,
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
        print(
            "ALPHA4_NETWORK_PYTHON_AIRGAP_IDENTITY_SENSITIVITY="
            f"{coverage['sensitivity_cases']}/26 PASS"
        )
        print(f"ALPHA4_NETWORK_PYTHON_AIRGAP_GRAND_TOTAL={coverage['grand_total_cases']}/472 PASS")
        print("ALPHA4_NETWORK_PYTHON_COMPANION_RUNTIME_CAPABILITY_ISOLATION=PASS")
        print("ALPHA4_NETWORK_PYTHON_COMPANION_PROCESS_ISOLATION=NOT_CLAIMED")
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
