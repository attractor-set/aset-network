from __future__ import annotations

import itertools
import re
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools import alpha4_network_profile_paired_expression as profile_pair
from tools.alpha4_network_causal_expression import (
    EXPECTED_CAUSAL_CONTRACTS,
    CausalExpressionError,
    CausalNet,
    causal_admit,
    causal_exact_observation,
    load_causal_nets,
    predicate_value,
)
from tools.alpha4_network_manifest import parse_network_manifests
from tools.alpha4_network_paired_expression import (
    EXPECTED_STACK_EFFECTS as CORE_EXPECTED_STACK_EFFECTS,
)
from tools.alpha4_network_paired_expression import (
    bounded_pairing_check,
    exact_observation,
    field_sensitivity_check,
    operational_admit,
    relational_admit,
)
from tools.alpha4_network_paired_expression import (
    parse_operational_words as parse_core_operational_words,
)
from tools.alpha4_network_relational_expression import (
    federation_relational_edges_from_source,
    validate_all_relational_sources,
    validate_federation_identity_guards,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "network/alpha4/profiles"
FEDERATION_FORTH = PROFILES / "federation/operational/components.forth"
FEDERATION_TLA = PROFILES / "federation/formal/FederationRelations.tla"


class TriangulatedExpressionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TriangulatedExpressionError(message)


CORE_COMPONENTS = {
    "ASET-NETWORK-COMPONENT-ADMIT-FRESH",
    "ASET-NETWORK-COMPONENT-ADMIT-REPLAY",
    "ASET-NETWORK-COMPONENT-REJECT-CONFLICT",
}
DYNAMIC_APPLICABILITY = "ASET-NETWORK-DYNAMIC-APPLICABILITY"
DYNAMIC_STUTTER = "ASET-NETWORK-DYNAMIC-NETWORK-STUTTER"
LIVENESS_COMPONENTS = {
    "delivered": "ASET-NETWORK-LIVENESS-DELIVERY-CLAIM",
    "observed": "ASET-NETWORK-LIVENESS-OBSERVATION-CLAIM",
    "resolved": "ASET-NETWORK-LIVENESS-RESOLUTION-CLAIM",
    "terminal": "ASET-NETWORK-LIVENESS-TERMINAL-RESULT",
}
COMPOSITION_COMPONENTS = {
    "capabilities": "ASET-NETWORK-FEDERATION-LIVENESS-CAPABILITIES",
    "boundary": "ASET-NETWORK-FEDERATION-LIVENESS-BOUNDARY",
    "delivery": "ASET-NETWORK-FEDERATION-LIVENESS-DELIVERY-WITNESS",
    "observation": "ASET-NETWORK-FEDERATION-LIVENESS-OBSERVATION-WITNESS",
    "resolution": "ASET-NETWORK-FEDERATION-LIVENESS-RESOLUTION-WITNESS",
    "progress": "ASET-NETWORK-FEDERATION-LIVENESS-PROGRESS-WITNESS",
}
FEDERATION_COMPONENTS = {
    "genesis": "ASET-NETWORK-FEDERATION-GENESIS",
    "join": "ASET-NETWORK-MEMBER-JOIN",
    "grant": "ASET-NETWORK-ROUTE-GRANT",
    "export": "ASET-NETWORK-EXPORT-ARTIFACT",
    "suspend": "ASET-NETWORK-SUSPEND-ROUTE",
    "withdraw": "ASET-NETWORK-MEMBER-WITHDRAW",
}

FEDERATION_EXPECTED_WORDS = {
    "FEDERATION-GENESIS": (
        "EMPTY-FEDERATION?",
        "CREATE-FEDERATION",
        "KEEP-NETWORK",
        "FEDERATION-CREATED",
    ),
    "MEMBER-JOIN": (
        "FEDERATION?",
        "MEMBER-ABSENT?",
        "ADD-MEMBER",
        "KEEP-NETWORK",
        "MEMBER-JOINED",
    ),
    "ROUTE-GRANT": (
        "ACTIVE-MEMBERS?",
        "DISTINCT-ENDPOINTS?",
        "ROUTE-ABSENT?",
        "ADD-ACTIVE-ROUTE",
        "KEEP-NETWORK",
        "ROUTE-GRANTED",
    ),
    "EXPORT-ARTIFACT": (
        "ACTIVE-ROUTE?",
        "EXPORT-ABSENT?",
        "ADD-EXPORT",
        "KEEP-NETWORK",
        "ARTIFACT-EXPORTED",
    ),
    "SUSPEND-ROUTE": (
        "ACTIVE-ROUTE?",
        "SUSPEND-ACTIVE-ROUTE",
        "KEEP-NETWORK",
        "ROUTE-SUSPENDED",
    ),
    "MEMBER-WITHDRAW": (
        "ACTIVE-MEMBER?",
        "NO-ACTIVE-ROUTE?",
        "WITHDRAW-MEMBER",
        "KEEP-NETWORK",
        "MEMBER-WITHDRAWN",
    ),
}

FEDERATION_EXPECTED_STACK_EFFECTS = {
    "FEDERATION-GENESIS": (
        ("profile", "federation-id", "epoch", "network"),
        ("profile", "network", "result"),
    ),
    "MEMBER-JOIN": (("profile", "context", "network"), ("profile", "network", "result")),
    "ROUTE-GRANT": (
        ("profile", "source", "target", "network"),
        ("profile", "network", "result"),
    ),
    "EXPORT-ARTIFACT": (
        ("profile", "source", "target", "artifact", "network"),
        ("profile", "network", "result"),
    ),
    "SUSPEND-ROUTE": (
        ("profile", "source", "target", "network"),
        ("profile", "network", "result"),
    ),
    "MEMBER-WITHDRAW": (
        ("profile", "context", "network"),
        ("profile", "network", "result"),
    ),
}


def _parse_forth(path: Path) -> dict[str, tuple[str, ...]]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r":\s+(?P<word>[A-Z0-9?-]+)\s+"
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
    require(stacks == FEDERATION_EXPECTED_STACK_EFFECTS, "federation stack contract drift")
    return words


def _validate_representation_sources() -> int:
    plan = parse_network_manifests(ROOT)
    for subject in plan.subjects:
        sources = (subject.operational, subject.relational, subject.causal_model)
        require(
            len(set(sources)) == 3,
            f"representation sources are not independent paths: {subject.name}",
        )
        for source in sources:
            require((ROOT / source).is_file(), f"bound representation source missing: {source}")
    return validate_all_relational_sources(ROOT)


def _interface_validator_independence() -> int:
    valid = {
        "import_id": "i0",
        "source_context": "s0",
        "target_context": "t0",
        "evidence_digest": "sha256:" + "0" * 64,
    }
    invalid = [
        {**valid, "evidence_digest": "NOT-A-SHA256"},
        {key: value for key, value in valid.items() if key != "source_context"},
        {**valid, "extra": "x"},
    ]
    require(
        exact_observation(valid) and causal_exact_observation(valid),
        "valid interface record rejected",
    )
    checks = 1
    for value in invalid:
        require(
            exact_observation(value) == causal_exact_observation(value) is False,
            "operational/causal interface validators disagree",
        )
        checks += 1
    return checks


def _core_triangulation(net: CausalNet) -> tuple[int, int]:
    paired_checks, paired_accepted = bounded_pairing_check()
    require(set(net.by_component()) == CORE_COMPONENTS, "core causal component set mismatch")
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
    states.extend([[deepcopy(item)] for item in observations])
    checks = 0
    accepted = 0
    for state in states:
        for observation in observations:
            operational = operational_admit(state, observation)
            relational = relational_admit(state, observation)
            causal = causal_admit(state, observation, net)
            require(operational == relational == causal, "core three-way observation mismatch")
            accepted += int(operational[1]["accepted"])
            checks += 1
    require(checks == paired_checks, "core pairing/triangulation case-count mismatch")
    require(accepted == paired_accepted, "core pairing/triangulation accepted-count mismatch")
    return checks, accepted


def _dynamic_triangulation(net: CausalNet) -> int:
    profile_pair.require_words(profile_pair.DYNAMIC_FORTH, profile_pair.EXPECTED_DYNAMIC_WORDS)
    checks = 0
    for exact_binding, recognition in itertools.product(
        (False, True), ("UNKNOWN", "ALLOW", "BLOCK")
    ):
        facts = set()
        if exact_binding:
            facts.add("EXACT_PROFILE_BINDING")
        if recognition == "ALLOW":
            facts.add("TARGET_LOCAL_ALLOW")
        values = (
            profile_pair.dynamic_operational_applicable(exact_binding, recognition),
            profile_pair.dynamic_relational_applicable(exact_binding, recognition),
            predicate_value(net, DYNAMIC_APPLICABILITY, facts),
        )
        require(values[0] == values[1] == values[2], "dynamic applicability three-way mismatch")
        checks += 1
    for before, after in itertools.product(("n0", "n1"), repeat=2):
        facts = {"SAME_NETWORK"} if before == after else set()
        values = (
            profile_pair.dynamic_operational_stutter(before, after),
            profile_pair.dynamic_relational_stutter(before, after),
            predicate_value(net, DYNAMIC_STUTTER, facts),
        )
        require(values[0] == values[1] == values[2], "dynamic stutter three-way mismatch")
        checks += 1
    return checks


def _liveness_triangulation(net: CausalNet) -> int:
    profile_pair.require_words(profile_pair.LIVENESS_FORTH, profile_pair.EXPECTED_LIVENESS_WORDS)
    checks = 0
    functions = (
        (
            profile_pair.liveness_operational_delivered,
            profile_pair.liveness_relational_delivered,
            LIVENESS_COMPONENTS["delivered"],
        ),
        (
            profile_pair.liveness_operational_observed,
            profile_pair.liveness_relational_observed,
            LIVENESS_COMPONENTS["observed"],
        ),
        (
            profile_pair.liveness_operational_resolved,
            profile_pair.liveness_relational_resolved,
            LIVENESS_COMPONENTS["resolved"],
        ),
    )
    for assumptions in profile_pair._powerset(profile_pair.LIVENESS_ASSUMPTIONS):
        for operational, relational, component_id in functions:
            values = (
                operational(assumptions),
                relational(assumptions),
                predicate_value(net, component_id, set(assumptions)),
            )
            require(values[0] == values[1] == values[2], "liveness three-way claim mismatch")
            checks += 1
    for result in ("UNKNOWN", "ALLOW", "BLOCK"):
        facts = {"SEED_TERMINAL_RESULT"} if result in profile_pair.SEED_TERMINAL_RESULTS else set()
        values = (
            profile_pair.liveness_operational_result_permitted(result),
            profile_pair.liveness_relational_result_permitted(result),
            predicate_value(net, LIVENESS_COMPONENTS["terminal"], facts),
        )
        require(values[0] == values[1] == values[2], "liveness terminal-result three-way mismatch")
        checks += 1
    return checks


def _composition_triangulation(net: CausalNet) -> int:
    profile_pair.require_words(
        profile_pair.COMPOSITION_FORTH, profile_pair.EXPECTED_COMPOSITION_WORDS
    )
    checks = 0
    for provided in profile_pair._powerset(profile_pair.REQUIRED_CAPABILITIES):
        facts = (
            {"REQUIRED_CAPABILITIES_PRESENT"}
            if profile_pair.REQUIRED_CAPABILITIES <= provided
            else set()
        )
        values = (
            profile_pair.composition_operational_capabilities(provided),
            profile_pair.composition_relational_capabilities(provided),
            predicate_value(net, COMPOSITION_COMPONENTS["capabilities"], facts),
        )
        require(values[0] == values[1] == values[2], "composition capability three-way mismatch")
        checks += 1
    for values_in in itertools.product((False, True), repeat=4):
        parent, state, transition, authority = values_in
        facts = set()
        if not parent:
            facts.add("NO_PROFILE_PARENT")
        if not state:
            facts.add("NO_STATE_TRANSFER")
        if not transition:
            facts.add("NO_TRANSITION_TRANSFER")
        if not authority:
            facts.add("NO_AUTHORITY_TRANSFER")
        values = (
            profile_pair.composition_operational_boundary(*values_in),
            profile_pair.composition_relational_boundary(*values_in),
            predicate_value(net, COMPOSITION_COMPONENTS["boundary"], facts),
        )
        require(values[0] == values[1] == values[2], "composition boundary three-way mismatch")
        checks += 1

    export = "e0"
    membership_sets = (set(), {export})
    for exported, delivered, observed, resolved in itertools.product(membership_sets, repeat=4):
        facts = set()
        if export in exported:
            facts.add("EXPORTED")
        if export in delivered:
            facts.add("DELIVERED")
        if export in observed:
            facts.add("OBSERVED")
        if export in resolved:
            facts.add("RESOLVED")
        triples = (
            (
                profile_pair.composition_operational_delivery_witness(exported, delivered, export),
                profile_pair.composition_relational_delivery_witness(exported, delivered, export),
                predicate_value(net, COMPOSITION_COMPONENTS["delivery"], facts),
            ),
            (
                profile_pair.composition_operational_observation_witness(
                    delivered, observed, export
                ),
                profile_pair.composition_relational_observation_witness(
                    delivered, observed, export
                ),
                predicate_value(net, COMPOSITION_COMPONENTS["observation"], facts),
            ),
            (
                profile_pair.composition_operational_resolution_witness(observed, resolved, export),
                profile_pair.composition_relational_resolution_witness(observed, resolved, export),
                predicate_value(net, COMPOSITION_COMPONENTS["resolution"], facts),
            ),
            (
                profile_pair.composition_operational_progress_witness(
                    exported, delivered, observed, resolved, export
                ),
                profile_pair.composition_relational_progress_witness(
                    exported, delivered, observed, resolved, export
                ),
                predicate_value(net, COMPOSITION_COMPONENTS["progress"], facts),
            ),
        )
        for values in triples:
            require(values[0] == values[1] == values[2], "composition witness three-way mismatch")
            checks += 1
    return checks


FederationState = tuple[bool, int, int, int, bool]
FederationEdge = tuple[str, str, FederationState]


def _operational_federation_edges(state: FederationState) -> set[FederationEdge]:
    require(
        _parse_forth(FEDERATION_FORTH) == FEDERATION_EXPECTED_WORDS,
        "federation operational source drift",
    )
    created, a, b, route, exported = state
    out: set[FederationEdge] = set()
    if not created:
        out.add((FEDERATION_COMPONENTS["genesis"], "-", (True, a, b, route, exported)))
    if created and a == 0:
        out.add((FEDERATION_COMPONENTS["join"], "A", (created, 1, b, route, exported)))
    if created and b == 0:
        out.add((FEDERATION_COMPONENTS["join"], "B", (created, a, 1, route, exported)))
    if created and a == 1 and b == 1 and route == 0:
        out.add((FEDERATION_COMPONENTS["grant"], "A-B", (created, a, b, 1, exported)))
    if route == 1 and not exported:
        out.add((FEDERATION_COMPONENTS["export"], "A-B", (created, a, b, route, True)))
    if route == 1:
        out.add((FEDERATION_COMPONENTS["suspend"], "A-B", (created, a, b, 2, exported)))
    if a == 1 and route != 1:
        out.add((FEDERATION_COMPONENTS["withdraw"], "A", (created, 2, b, route, exported)))
    if b == 1 and route != 1:
        out.add((FEDERATION_COMPONENTS["withdraw"], "B", (created, a, 2, route, exported)))
    return out


def _relational_federation_edges(state: FederationState) -> set[FederationEdge]:
    return federation_relational_edges_from_source(state)


def _causal_federation_apply(
    state: FederationState, net: CausalNet, component_id: str, actor: str
) -> FederationState | None:
    transition = net.by_component()[component_id]
    created, a, b, route, exported = state
    facts: set[str] = set()
    if not created:
        facts.add("EMPTY_FEDERATION")
    if created:
        facts.add("FEDERATION_EXISTS")
    if actor == "A" and a == 0 or actor == "B" and b == 0:
        facts.add("MEMBER_ABSENT")
    if actor == "A" and a == 1 or actor == "B" and b == 1:
        facts.add("ACTIVE_MEMBER")
    if a == 1 and b == 1:
        facts.add("ACTIVE_MEMBERS")
    if actor == "A-B":
        facts.add("DISTINCT_ENDPOINTS")
    if route == 0:
        facts.add("ROUTE_ABSENT")
    if route == 1:
        facts.add("ACTIVE_ROUTE")
    if not exported:
        facts.add("EXPORT_ABSENT")
    if route != 1:
        facts.add("NO_ACTIVE_ROUTE")
    if not set(transition.requirements) <= facts:
        return None
    require(
        "PRESERVE_NETWORK" in transition.effects,
        f"{component_id}: Network-stutter effect missing",
    )
    target = [created, a, b, route, exported]
    for effect in transition.effects:
        if effect == "CREATE_FEDERATION":
            target[0] = True
        elif effect == "ADD_MEMBER":
            target[1 if actor == "A" else 2] = 1
        elif effect == "ADD_ACTIVE_ROUTE":
            target[3] = 1
        elif effect == "ADD_EXPORT":
            target[4] = True
        elif effect == "SUSPEND_ACTIVE_ROUTE":
            target[3] = 2
        elif effect == "WITHDRAW_MEMBER":
            target[1 if actor == "A" else 2] = 2
        elif effect == "PRESERVE_NETWORK":
            continue
        else:
            raise TriangulatedExpressionError(f"unsupported federation causal effect: {effect}")
    return tuple(target)


def _causal_federation_edges(state: FederationState, net: CausalNet) -> set[FederationEdge]:
    candidates = (
        (FEDERATION_COMPONENTS["genesis"], "-"),
        (FEDERATION_COMPONENTS["join"], "A"),
        (FEDERATION_COMPONENTS["join"], "B"),
        (FEDERATION_COMPONENTS["grant"], "A-B"),
        (FEDERATION_COMPONENTS["export"], "A-B"),
        (FEDERATION_COMPONENTS["suspend"], "A-B"),
        (FEDERATION_COMPONENTS["withdraw"], "A"),
        (FEDERATION_COMPONENTS["withdraw"], "B"),
    )
    out: set[FederationEdge] = set()
    for component_id, actor in candidates:
        target = _causal_federation_apply(state, net, component_id, actor)
        if target is not None:
            out.add((component_id, actor, target))
    return out


def _federation_triangulation(net: CausalNet) -> tuple[int, int]:
    initial: FederationState = (False, 0, 0, 0, False)
    queue = deque([initial])
    seen = {initial}
    edges = 0
    while queue:
        state = queue.popleft()
        operational = _operational_federation_edges(state)
        relational = _relational_federation_edges(state)
        causal = _causal_federation_edges(state, net)
        require(
            operational == relational == causal,
            f"federation three-way edge mismatch: {state!r}",
        )
        edges += len(operational)
        for _, _, target in operational:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    require(len(seen) == 20 and edges == 25, "federation bounded state-space drift")
    return len(seen), edges


def _validate_operational_causal_contracts(nets: dict[str, CausalNet]) -> tuple[int, int, int]:
    parse_core_operational_words()
    profile_pair.require_words(
        profile_pair.DYNAMIC_FORTH,
        profile_pair.EXPECTED_DYNAMIC_WORDS,
        profile_pair.EXPECTED_DYNAMIC_STACK_EFFECTS,
    )
    profile_pair.require_words(
        profile_pair.LIVENESS_FORTH,
        profile_pair.EXPECTED_LIVENESS_WORDS,
        profile_pair.EXPECTED_LIVENESS_STACK_EFFECTS,
    )
    profile_pair.require_words(
        profile_pair.COMPOSITION_FORTH,
        profile_pair.EXPECTED_COMPOSITION_WORDS,
        profile_pair.EXPECTED_COMPOSITION_STACK_EFFECTS,
    )
    federation_words = _parse_forth(FEDERATION_FORTH)
    require(federation_words == FEDERATION_EXPECTED_WORDS, "federation operational source drift")

    stack_contract_count = (
        len(CORE_EXPECTED_STACK_EFFECTS)
        + len(profile_pair.EXPECTED_DYNAMIC_STACK_EFFECTS)
        + len(FEDERATION_EXPECTED_STACK_EFFECTS)
        + len(profile_pair.EXPECTED_LIVENESS_STACK_EFFECTS)
        + len(profile_pair.EXPECTED_COMPOSITION_STACK_EFFECTS)
    )
    causal_contract_count = sum(len(items) for items in EXPECTED_CAUSAL_CONTRACTS.values())

    federation_by_symbol = {item.symbol: item for item in nets["federation"].transitions}
    result_bindings = 0
    for symbol, body in federation_words.items():
        operational_code = body[-1].replace("-", "_")
        causal_code = federation_by_symbol[symbol].output_map()["CODE"]
        require(
            operational_code == causal_code,
            f"{symbol}: operational/causal result-code mismatch",
        )
        result_bindings += 1
    return stack_contract_count, causal_contract_count, result_bindings


def check_triangulated_assurance(root: Path = ROOT) -> dict[str, Any]:
    require(root.resolve() == ROOT.resolve(), "alternate root is not supported by this checker")
    relational_derivations = _validate_representation_sources()
    federation_identity_guards = validate_federation_identity_guards(ROOT)
    interface_validator_cases = _interface_validator_independence()
    nets = load_causal_nets(root)
    stack_contracts, causal_contracts, result_bindings = _validate_operational_causal_contracts(
        nets
    )
    core_cases, accepted = _core_triangulation(nets["network"])
    core_field_sensitivity = field_sensitivity_check()
    dynamic_binding_sensitivity = profile_pair.bounded_dynamic_binding_field_sensitivity_check()
    composition_identity_sensitivity = profile_pair.bounded_composition_identity_sensitivity_check()
    dynamic_cases = _dynamic_triangulation(nets["dynamic"])
    federation_states, federation_edges = _federation_triangulation(nets["federation"])
    liveness_cases = _liveness_triangulation(nets["liveness"])
    composition_cases = _composition_triangulation(nets["federation-liveness"])
    total_cases = core_cases + dynamic_cases + federation_edges + liveness_cases + composition_cases
    return {
        "document_type": "aset-network-three-way-assurance-evidence",
        "profile_id": "ASET-NETWORK-ALPHA4-THREE-WAY-ASSURANCE-V1",
        "semantic_delta": "NONE",
        "semantic_precedence": "NONE",
        "representations": ("OPERATIONAL", "RELATIONAL", "CAUSAL"),
        "pairwise_relations": {
            "operational_relational": "PASS",
            "operational_causal": "PASS",
            "relational_causal": "PASS",
        },
        "operational_stack_contracts": stack_contracts,
        "causal_closed_world_contracts": causal_contracts,
        "federation_result_code_bindings": result_bindings,
        "relational_source_derivations": relational_derivations,
        "federation_identity_guard_derivations": federation_identity_guards,
        "interface_validator_cases": interface_validator_cases,
        "core_field_sensitivity": core_field_sensitivity,
        "dynamic_binding_sensitivity": dynamic_binding_sensitivity,
        "composition_identity_sensitivity": composition_identity_sensitivity,
        "core_cases": core_cases,
        "core_accepted": accepted,
        "dynamic_cases": dynamic_cases,
        "federation_states": federation_states,
        "federation_edges": federation_edges,
        "liveness_cases": liveness_cases,
        "composition_cases": composition_cases,
        "total_cases": total_cases,
        "status": "PASS",
    }


def print_evidence(evidence: dict[str, Any]) -> None:
    core = evidence["core_cases"]
    dynamic = evidence["dynamic_cases"]
    fed_edges = evidence["federation_edges"]
    fed_states = evidence["federation_states"]
    liveness = evidence["liveness_cases"]
    composition = evidence["composition_cases"]
    total = evidence["total_cases"]
    stacks = evidence["operational_stack_contracts"]
    causal_contracts = evidence["causal_closed_world_contracts"]
    result_bindings = evidence["federation_result_code_bindings"]
    relational_derivations = evidence["relational_source_derivations"]
    federation_identity_guards = evidence["federation_identity_guard_derivations"]
    interface_validator_cases = evidence["interface_validator_cases"]
    core_field_sensitivity = evidence["core_field_sensitivity"]
    dynamic_binding_sensitivity = evidence["dynamic_binding_sensitivity"]
    composition_identity_sensitivity = evidence["composition_identity_sensitivity"]
    print("ALPHA4_NETWORK_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
    print("ALPHA4_NETWORK_SEMANTIC_PRECEDENCE=NONE")
    print(f"ALPHA4_NETWORK_OPERATIONAL_RELATIONAL_CONGRUENCE={core}/{core} PASS")
    print(f"ALPHA4_NETWORK_OPERATIONAL_CAUSAL_CONGRUENCE={core}/{core} PASS")
    print(f"ALPHA4_NETWORK_RELATIONAL_CAUSAL_CONGRUENCE={core}/{core} PASS")
    print(f"ALPHA4_NETWORK_TRIANGULATED_RUNTIME_CONGRUENCE={core}/{core} PASS")
    print(f"ALPHA4_DYNAMIC_THREE_WAY_CONGRUENCE={dynamic}/{dynamic} PASS")
    print(f"ALPHA4_FEDERATION_THREE_WAY_CONGRUENCE=STATES:{fed_states} EDGES:{fed_edges} PASS")
    print(f"ALPHA4_LIVENESS_THREE_WAY_CONGRUENCE={liveness}/{liveness} PASS")
    print(f"ALPHA4_FEDERATION_LIVENESS_THREE_WAY_CONGRUENCE={composition}/{composition} PASS")
    print(f"ALPHA4_NETWORK_ALL_SUBJECTS_TRIANGULATED_CASES={total}/{total} PASS")
    print(f"ALPHA4_NETWORK_OPERATIONAL_STACK_CONTRACTS={stacks}/{stacks} PASS")
    print(
        f"ALPHA4_NETWORK_CAUSAL_CLOSED_WORLD_CONTRACTS={causal_contracts}/{causal_contracts} PASS"
    )
    print(
        "ALPHA4_FEDERATION_OPERATIONAL_CAUSAL_RESULT_CODES="
        f"{result_bindings}/{result_bindings} PASS"
    )
    print(
        "ALPHA4_NETWORK_RELATIONAL_SOURCE_DERIVATIONS="
        f"{relational_derivations}/{relational_derivations} PASS"
    )
    print(
        "ALPHA4_FEDERATION_IDENTITY_GUARD_DERIVATIONS="
        f"{federation_identity_guards}/{federation_identity_guards} PASS"
    )
    print(
        "ALPHA4_NETWORK_INTERFACE_VALIDATOR_INDEPENDENCE="
        f"{interface_validator_cases}/{interface_validator_cases} PASS"
    )
    print(
        "ALPHA4_NETWORK_CORE_FIELD_SENSITIVITY="
        f"{core_field_sensitivity}/{core_field_sensitivity} PASS"
    )
    print(
        "ALPHA4_DYNAMIC_BINDING_FIELD_SENSITIVITY="
        f"{dynamic_binding_sensitivity}/{dynamic_binding_sensitivity} PASS"
    )
    print(
        "ALPHA4_FEDERATION_LIVENESS_IDENTITY_SENSITIVITY="
        f"{composition_identity_sensitivity}/{composition_identity_sensitivity} PASS"
    )
    print("ALPHA4_NETWORK_REPRESENTATION_SOURCE_INDEPENDENCE=PASS")
    print("ALPHA4_NETWORK_TRIANGULATED_EXPRESSION=PASS")


def main() -> int:
    try:
        evidence = check_triangulated_assurance(ROOT)
        print_evidence(evidence)
        return 0
    except (
        AssertionError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        CausalExpressionError,
        TriangulatedExpressionError,
    ) as error:
        print(f"ALPHA4_NETWORK_TRIANGULATED_EXPRESSION_ERROR={error}")
        print("ALPHA4_NETWORK_TRIANGULATED_EXPRESSION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
