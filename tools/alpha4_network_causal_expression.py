from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.alpha4_network_paired_expression import exact_observation

ROOT = Path(__file__).resolve().parents[1]


class CausalExpressionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CausalExpressionError(message)


@dataclass(frozen=True)
class CausalTransition:
    symbol: str
    component_id: str
    requirements: tuple[str, ...]
    effects: tuple[str, ...]
    outputs: tuple[tuple[str, str], ...]

    def output_map(self) -> dict[str, str]:
        return dict(self.outputs)


@dataclass(frozen=True)
class CausalNet:
    schema_version: int
    subject_id: str
    semantic_precedence: str
    mode: str
    transitions: tuple[CausalTransition, ...]

    def by_component(self) -> dict[str, CausalTransition]:
        return {item.component_id: item for item in self.transitions}


SUBJECTS = {
    "network": (
        Path("network/alpha4/NETWORK.aset"),
        Path("network/alpha4/causal/components.petri"),
        "ASET-NETWORK-ALPHA4-CAUSAL",
        "STATE-TRANSITION",
    ),
    "dynamic": (
        Path("network/alpha4/profiles/dynamic/DYNAMIC.aset"),
        Path("network/alpha4/profiles/dynamic/causal/components.petri"),
        "ASET-NETWORK-DYNAMIC-ALPHA4-CAUSAL",
        "PREDICATE",
    ),
    "federation": (
        Path("network/alpha4/profiles/federation/FEDERATION.aset"),
        Path("network/alpha4/profiles/federation/causal/components.petri"),
        "ASET-NETWORK-FEDERATION-ALPHA4-CAUSAL",
        "STATE-TRANSITION",
    ),
    "liveness": (
        Path("network/alpha4/profiles/liveness/LIVENESS.aset"),
        Path("network/alpha4/profiles/liveness/causal/components.petri"),
        "ASET-NETWORK-LIVENESS-ALPHA4-CAUSAL",
        "PREDICATE",
    ),
    "federation-liveness": (
        Path("network/alpha4/profiles/composition/federation-liveness/FEDERATION_LIVENESS.aset"),
        Path("network/alpha4/profiles/composition/federation-liveness/causal/components.petri"),
        "ASET-NETWORK-FEDERATION-LIVENESS-ALPHA4-CAUSAL",
        "PREDICATE",
    ),
}


def _lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_causal_net(path: Path, expected_subject: str, expected_mode: str) -> CausalNet:
    lines = _lines(path)
    require(lines, f"empty causal source: {path}")
    head = lines[0].split()
    require(
        len(head) == 3 and head[0] == "ASET-CAUSAL-NET",
        f"invalid causal header: {path}",
    )
    schema_version = int(head[1])
    subject_id = head[2]
    require(schema_version == 1, f"unsupported causal schema: {path}")
    require(subject_id == expected_subject, f"causal subject mismatch: {path}")

    semantic_precedence = ""
    mode = ""
    transitions: list[CausalTransition] = []
    index = 1
    while index < len(lines):
        tokens = lines[index].split()
        kind = tokens[0]
        if kind == "SEMANTIC-PRECEDENCE":
            require(len(tokens) == 2 and not semantic_precedence, "invalid causal precedence")
            semantic_precedence = tokens[1]
            index += 1
            continue
        if kind == "MODE":
            require(len(tokens) == 2 and not mode, "invalid causal mode")
            mode = tokens[1]
            index += 1
            continue
        require(
            kind == "TRANSITION" and len(tokens) == 3,
            f"invalid causal statement: {lines[index]}",
        )
        symbol, component_id = tokens[1], tokens[2]
        requirements: list[str] = []
        effects: list[str] = []
        outputs: list[tuple[str, str]] = []
        index += 1
        while index < len(lines) and lines[index] != "END":
            body = lines[index].split()
            require(body, f"empty causal transition statement: {path}")
            if body[0] == "REQUIRE":
                require(len(body) == 2, f"{symbol}: invalid REQUIRE")
                requirements.append(body[1])
            elif body[0] == "EFFECT":
                require(len(body) == 2, f"{symbol}: invalid EFFECT")
                effects.append(body[1])
            elif body[0] == "OUTPUT":
                require(len(body) == 3, f"{symbol}: invalid OUTPUT")
                outputs.append((body[1], body[2]))
            else:
                raise CausalExpressionError(f"{symbol}: unsupported statement: {body[0]}")
            index += 1
        require(index < len(lines) and lines[index] == "END", f"{symbol}: END missing")
        require(len(set(requirements)) == len(requirements), f"{symbol}: duplicate requirement")
        require(len(set(effects)) == len(effects), f"{symbol}: duplicate effect")
        require(len({key for key, _ in outputs}) == len(outputs), f"{symbol}: duplicate output")
        transitions.append(
            CausalTransition(
                symbol=symbol,
                component_id=component_id,
                requirements=tuple(requirements),
                effects=tuple(effects),
                outputs=tuple(outputs),
            )
        )
        index += 1

    require(semantic_precedence == "NONE", f"causal precedence must be NONE: {path}")
    require(mode == expected_mode, f"causal mode mismatch: {path}")
    require(transitions, f"causal transitions missing: {path}")
    require(
        len({item.symbol for item in transitions}) == len(transitions),
        f"duplicate causal transition symbol: {path}",
    )
    require(
        len({item.component_id for item in transitions}) == len(transitions),
        f"duplicate causal component id: {path}",
    )
    return CausalNet(schema_version, subject_id, semantic_precedence, mode, tuple(transitions))


def _manifest_causal_bindings(path: Path) -> tuple[str, dict[str, str]]:
    model = ""
    bindings: dict[str, str] = {}
    for line in _lines(path):
        tokens = line.split()
        if tokens[0] == "CAUSAL-MODEL":
            require(len(tokens) == 2 and not model, f"invalid CAUSAL-MODEL: {path}")
            model = tokens[1]
        elif tokens[0] == "CAUSAL-BIND":
            require(len(tokens) == 3, f"invalid CAUSAL-BIND: {path}")
            require(tokens[1] not in bindings, f"duplicate CAUSAL-BIND: {path}")
            bindings[tokens[1]] = tokens[2]
    require(model, f"CAUSAL-MODEL missing: {path}")
    require(bindings, f"CAUSAL-BIND missing: {path}")
    return model, bindings


def load_causal_nets(root: Path = ROOT) -> dict[str, CausalNet]:
    nets: dict[str, CausalNet] = {}
    for key, (manifest_rel, causal_rel, subject_id, mode) in SUBJECTS.items():
        manifest = root / manifest_rel
        causal = root / causal_rel
        require(manifest.is_file(), f"manifest missing: {manifest_rel}")
        require(causal.is_file(), f"causal source missing: {causal_rel}")
        model, bindings = _manifest_causal_bindings(manifest)
        require(model == causal_rel.as_posix(), f"causal model binding mismatch: {key}")
        net = parse_causal_net(causal, subject_id, mode)
        actual = {item.component_id: item.symbol for item in net.transitions}
        require(actual == bindings, f"causal component binding mismatch: {key}")
        nets[key] = net
    return nets


def predicate_value(net: CausalNet, component_id: str, facts: set[str]) -> bool:
    try:
        transition = net.by_component()[component_id]
    except KeyError as error:
        raise CausalExpressionError(f"unknown causal component: {component_id}") from error
    return set(transition.requirements) <= facts


def _bool(value: str) -> bool:
    require(value in {"TRUE", "FALSE"}, f"invalid causal boolean: {value}")
    return value == "TRUE"


def causal_admit(
    imports: list[dict[str, Any]], observation: dict[str, Any], net: CausalNet
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not exact_observation(observation):
        return deepcopy(imports), {
            "accepted": False,
            "code": "INVALID_IMPORT",
            "state_changed": False,
            "seed_projection": {"recognition": "NOT_APPLICABLE", "effect_permitted": False},
        }
    same_id = [item for item in imports if item["import_id"] == observation["import_id"]]
    facts = {"EXACT_IMPORT"}
    if not same_id:
        facts.add("FRESH_ID")
    elif observation in same_id:
        facts.add("EXACT_REPLAY")
    else:
        facts.add("CONFLICTING_ID")

    enabled = [item for item in net.transitions if set(item.requirements) <= facts]
    require(len(enabled) == 1, f"core causal classification is not singular: {facts!r}")
    transition = enabled[0]
    outputs = transition.output_map()
    new_state = deepcopy(imports)
    if "ADD_IMPORT" in transition.effects:
        new_state.append(deepcopy(observation))
    elif "PRESERVE_IMPORTS" not in transition.effects:
        raise CausalExpressionError(f"unsupported core causal effect: {transition.effects!r}")
    require(
        outputs.get("SEED_EFFECT") == "FALSE",
        "Network causal line crossed Seed effect boundary",
    )
    return new_state, {
        "accepted": _bool(outputs["ACCEPTED"]),
        "code": outputs["CODE"],
        "state_changed": _bool(outputs["STATE_CHANGED"]),
        "seed_projection": {
            "recognition": outputs["SEED_RECOGNITION"],
            "effect_permitted": _bool(outputs["SEED_EFFECT"]),
        },
    }


def main() -> int:
    nets = load_causal_nets(ROOT)
    counts = {key: len(net.transitions) for key, net in nets.items()}
    print("ALPHA4_NETWORK_CAUSAL_SUBJECTS=5/5 PASS")
    print(f"ALPHA4_NETWORK_CAUSAL_COMPONENTS={counts['network']}/{counts['network']} PASS")
    print(f"ALPHA4_DYNAMIC_CAUSAL_COMPONENTS={counts['dynamic']}/{counts['dynamic']} PASS")
    print(f"ALPHA4_FEDERATION_CAUSAL_COMPONENTS={counts['federation']}/{counts['federation']} PASS")
    print(f"ALPHA4_LIVENESS_CAUSAL_COMPONENTS={counts['liveness']}/{counts['liveness']} PASS")
    print(
        "ALPHA4_FEDERATION_LIVENESS_CAUSAL_COMPONENTS="
        f"{counts['federation-liveness']}/{counts['federation-liveness']} PASS"
    )
    print("ALPHA4_NETWORK_CAUSAL_SEMANTIC_PRECEDENCE=NONE")
    print("ALPHA4_NETWORK_CAUSAL_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
