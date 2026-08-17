from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.alpha4_network_manifest import SubjectBinding, parse_network_manifests

ROOT = Path(__file__).resolve().parents[1]


class RelationalExpressionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RelationalExpressionError(message)


def strip_tla_comments(text: str) -> str:
    without_blocks = re.sub(r"\(\*.*?\*\)", "", text, flags=re.DOTALL)
    return re.sub(r"(?m)\\\*.*$", "", without_blocks)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _source_text(root: Path, subject: SubjectBinding) -> str:
    return strip_tla_comments((root / subject.relational).read_text(encoding="utf-8"))


def extract_operator(text: str, operator: str) -> tuple[tuple[str, ...], str]:
    pattern = re.compile(
        rf"(?ms)^{re.escape(operator)}\((?P<args>[^)]*)\)\s*==\s*(?P<body>.*?)"
        rf"(?=^[A-Z][A-Za-z0-9_]*\([^)]*\)\s*==|^[A-Z][A-Za-z0-9_]*\s*==|^=+)"
    )
    match = pattern.search(text)
    if match is None:
        raise RelationalExpressionError(f"formal operator missing: {operator}")
    args = tuple(item.strip() for item in match.group("args").split(",") if item.strip())
    return args, compact(match.group("body"))


def extract_value_operator(text: str, operator: str) -> str:
    pattern = re.compile(
        rf"(?ms)^{re.escape(operator)}\s*==\s*(?P<body>.*?)"
        rf"(?=^[A-Z][A-Za-z0-9_]*\([^)]*\)\s*==|^[A-Z][A-Za-z0-9_]*\s*==|^=+)"
    )
    match = pattern.search(text)
    if match is None:
        raise RelationalExpressionError(f"formal value missing: {operator}")
    return compact(match.group("body"))


def _quoted_set(body: str) -> frozenset[str]:
    require(body.startswith("{") and body.endswith("}"), f"unsupported set expression: {body}")
    return frozenset(re.findall(r'"([A-Z0-9_]+)"', body))


@dataclass(frozen=True)
class CoreRule:
    component_id: str
    operator: str
    classifier: str
    effect: str
    result_code: str


@dataclass(frozen=True)
class CoreContract:
    observation_fields: tuple[str, ...]
    identifier_field: str
    accepted_results: frozenset[str]
    rules: tuple[CoreRule, ...]


def derive_core_contract(root: Path = ROOT) -> CoreContract:
    subject = parse_network_manifests(root).by_name()["network"]
    text = _source_text(root, subject)
    universe = extract_value_operator(text, "ObservationUniverse")
    fields = tuple(re.findall(r"([a-z_]+):[A-Za-z][A-Za-z0-9_]*", universe))
    require(fields, "ObservationUniverse fields missing")

    _, same_body = extract_operator(text, "SameIdentifier")
    same_match = re.fullmatch(r"\{x\\ins:x\.([a-z_]+)=o\.([a-z_]+)\}", same_body)
    require(same_match is not None, "SameIdentifier relational form unsupported")
    require(same_match.group(1) == same_match.group(2), "SameIdentifier field asymmetry")
    identifier_field = same_match.group(1)
    require(identifier_field in fields, "SameIdentifier field absent from ObservationUniverse")

    _, fresh = extract_operator(text, "FreshIdentifier")
    require(fresh == "SameIdentifier(s,o)={}", "FreshIdentifier semantics drift")
    _, replay = extract_operator(text, "ExactReplay")
    require(replay == "o\\ins", "ExactReplay semantics drift")
    _, conflict = extract_operator(text, "ConflictingIdentifier")
    require(
        conflict
        in {
            "/\\SameIdentifier(s,o)#{} /\\o\\notins".replace(" ", ""),
            "/\\SameIdentifier(s,o)#{}\\/\\o\\notins".replace("\\/", ""),
        }
        or ("SameIdentifier(s,o)#{}" in conflict and "o\\notins" in conflict),
        "ConflictingIdentifier semantics drift",
    )

    accepted = _quoted_set(extract_operator(text, "AcceptedResult")[1].split("\\in", 1)[1])
    _, effect_body = extract_operator(text, "SeedProjectionEffectPermitted")
    require(effect_body == "FALSE", "SeedProjectionEffectPermitted must remain FALSE")

    rules: list[CoreRule] = []
    for pair in subject.pairs:
        _, body = extract_operator(text, pair.formal_operator)
        require("s\\inStateType" in body, f"{pair.formal_operator}: StateType precondition missing")
        require(
            "o\\inObservationUniverse" in body,
            f"{pair.formal_operator}: ObservationUniverse precondition missing",
        )
        classifiers = [
            name
            for name, marker in (
                ("FRESH", "FreshIdentifier(s,o)"),
                ("REPLAY", "ExactReplay(s,o)"),
                ("CONFLICT", "ConflictingIdentifier(s,o)"),
            )
            if marker in body
        ]
        require(len(classifiers) == 1, f"{pair.formal_operator}: classifier not singular")
        if "t=s\\cup{o}" in body:
            effect = "ADD"
        elif "t=s" in body:
            effect = "PRESERVE"
        else:
            raise RelationalExpressionError(f"{pair.formal_operator}: state effect unsupported")
        result = re.search(r'result="([A-Z0-9_]+)"', body)
        require(result is not None, f"{pair.formal_operator}: result code missing")
        rules.append(
            CoreRule(
                pair.component_id, pair.formal_operator, classifiers[0], effect, result.group(1)
            )
        )
    return CoreContract(fields, identifier_field, accepted, tuple(rules))


def _result(accepted: bool, code: str, changed: bool) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "seed_projection": {
            "recognition": "UNKNOWN" if accepted else "NOT_APPLICABLE",
            "effect_permitted": False,
        },
    }


def relational_admit_from_source(
    imports: list[dict[str, Any]], observation: dict[str, Any], root: Path = ROOT
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = derive_core_contract(root)
    require(
        set(observation) == set(contract.observation_fields),
        "relational observation field surface mismatch",
    )
    identifier_exists = any(
        item[contract.identifier_field] == observation[contract.identifier_field]
        for item in imports
    )
    exact_replay = observation in imports
    classifier = "REPLAY" if exact_replay else "CONFLICT" if identifier_exists else "FRESH"
    matches = [rule for rule in contract.rules if rule.classifier == classifier]
    require(len(matches) == 1, f"core relational classification not singular: {classifier}")
    rule = matches[0]
    state = deepcopy(imports)
    if rule.effect == "ADD":
        state.append(deepcopy(observation))
    accepted = rule.result_code in contract.accepted_results
    return state, _result(accepted, rule.result_code, rule.effect == "ADD")


@dataclass(frozen=True)
class DynamicContract:
    projection: tuple[tuple[str, str], ...]
    recognition: str
    stutter_relation: str


def derive_dynamic_contract(root: Path = ROOT) -> DynamicContract:
    subject = parse_network_manifests(root).by_name()["dynamic"]
    text = _source_text(root, subject)
    _, project = extract_operator(text, "ProjectSeedBinding")
    mappings = tuple(re.findall(r"([a-z_]+)\|->binding\.([a-z_]+)", project))
    require(len(mappings) == 5, "dynamic projection field mapping drift")
    _, applicable = extract_operator(text, "ProfileApplicable")
    require(
        "seedBinding=ProjectSeedBinding(binding)" in applicable,
        "dynamic exact binding guard missing",
    )
    recognition = re.search(r'recognition="(UNKNOWN|ALLOW|BLOCK)"', applicable)
    require(recognition is not None, "dynamic recognition guard missing")
    _, stutter = extract_operator(text, "DynamicProfileNetworkProjection")
    if stutter == "networkAfter=networkBefore":
        relation = "EQ"
    elif stutter == "networkAfter#networkBefore":
        relation = "NEQ"
    else:
        raise RelationalExpressionError("dynamic Network projection relation unsupported")
    return DynamicContract(mappings, recognition.group(1), relation)


def project_seed_binding_from_source(binding: dict[str, str], root: Path = ROOT) -> dict[str, str]:
    contract = derive_dynamic_contract(root)
    return {target: binding[source] for target, source in contract.projection}


def dynamic_relational_applicable_from_source(
    binding: dict[str, str], seed_binding: dict[str, str], recognition: str, root: Path = ROOT
) -> bool:
    contract = derive_dynamic_contract(root)
    return (
        seed_binding == project_seed_binding_from_source(binding, root)
        and recognition == contract.recognition
    )


def dynamic_relational_stutter_from_source(before: str, after: str, root: Path = ROOT) -> bool:
    relation = derive_dynamic_contract(root).stutter_relation
    return after == before if relation == "EQ" else after != before


@dataclass(frozen=True)
class LivenessContract:
    assumptions_by_operator: tuple[tuple[str, frozenset[str]], ...]
    terminal_results: frozenset[str]


def derive_liveness_contract(root: Path = ROOT) -> LivenessContract:
    subject = parse_network_manifests(root).by_name()["liveness"]
    text = _source_text(root, subject)
    terminal_results = _quoted_set(extract_value_operator(text, "SeedTerminalResults"))
    predicates: list[tuple[str, frozenset[str]]] = []
    for pair in subject.pairs:
        _, body = extract_operator(text, pair.formal_operator)
        if pair.formal_operator == "ResolvedResultPermitted":
            require(
                body == "result\\inSeedTerminalResults", "liveness terminal-result semantics drift"
            )
            continue
        marker = "\\subseteqassumptions"
        require(marker in body, f"{pair.formal_operator}: assumptions subset relation missing")
        required = _quoted_set(body.split(marker, 1)[0])
        predicates.append((pair.formal_operator, required))
    return LivenessContract(tuple(predicates), terminal_results)


def liveness_relational_claim_from_source(
    operator: str, assumptions: set[str], root: Path = ROOT
) -> bool:
    index = dict(derive_liveness_contract(root).assumptions_by_operator)
    require(operator in index, f"unknown liveness operator: {operator}")
    return index[operator] <= assumptions


def liveness_relational_result_from_source(result: str, root: Path = ROOT) -> bool:
    return result in derive_liveness_contract(root).terminal_results


@dataclass(frozen=True)
class CompositionContract:
    required_capabilities: frozenset[str]
    boundary_false_args: frozenset[str]
    witness_memberships: tuple[tuple[str, tuple[str, ...]], ...]
    progress_dependencies: tuple[str, ...]


def derive_composition_contract(root: Path = ROOT) -> CompositionContract:
    subjects = parse_network_manifests(root).by_name()
    liveness_text = _source_text(root, subjects["liveness"])
    required = _quoted_set(extract_value_operator(liveness_text, "RequiredCapabilities"))
    text = _source_text(root, subjects["federation-liveness"])
    _, capabilities = extract_operator(text, "ProvidesRequiredCapabilities")
    require(
        capabilities == "RequiredCapabilities\\subseteqprovided",
        "composition capability semantics drift",
    )
    args, boundary = extract_operator(text, "CompositionBoundaryPreserved")
    false_args = frozenset(arg for arg in args if f"{arg}=FALSE" in boundary)
    require(false_args == frozenset(args), "composition boundary no-transfer clause drift")
    memberships: list[tuple[str, tuple[str, ...]]] = []
    for operator in ("DeliveryWitness", "ObservationWitness", "ResolutionWitness"):
        _, body = extract_operator(text, operator)
        containers = tuple(re.findall(r"export\\in([a-z]+)", body))
        require(len(containers) == 2, f"{operator}: exact witness membership surface drift")
        memberships.append((operator, containers))
    _, progress = extract_operator(text, "ProgressWitness")
    deps = tuple(
        name
        for name in ("DeliveryWitness", "ObservationWitness", "ResolutionWitness")
        if f"{name}(" in progress
    )
    require(deps, "ProgressWitness dependencies missing")
    return CompositionContract(required, false_args, tuple(memberships), deps)


def composition_relational_capabilities_from_source(provided: set[str], root: Path = ROOT) -> bool:
    return derive_composition_contract(root).required_capabilities <= provided


def composition_relational_boundary_from_source(
    parent_relation: bool,
    state_transfer: bool,
    transition_transfer: bool,
    authority_transfer: bool,
    root: Path = ROOT,
) -> bool:
    values = {
        "parentRelation": parent_relation,
        "stateOwnershipTransferred": state_transfer,
        "transitionOwnershipTransferred": transition_transfer,
        "authorityTransferred": authority_transfer,
    }
    contract = derive_composition_contract(root)
    return all(values[arg] is False for arg in contract.boundary_false_args)


def composition_relational_witness_from_source(
    operator: str, containers: dict[str, set[str]], export: str, root: Path = ROOT
) -> bool:
    index = dict(derive_composition_contract(root).witness_memberships)
    require(operator in index, f"unknown composition witness: {operator}")
    return all(export in containers[name] for name in index[operator])


def composition_relational_progress_from_source(
    exported: set[str],
    delivered: set[str],
    observed: set[str],
    resolved: set[str],
    export: str,
    root: Path = ROOT,
) -> bool:
    containers = {
        "exported": exported,
        "delivered": delivered,
        "observed": observed,
        "resolved": resolved,
    }
    contract = derive_composition_contract(root)
    return all(
        composition_relational_witness_from_source(dep, containers, export, root)
        for dep in contract.progress_dependencies
    )


MEMBER_STATE = {"ABSENT": 0, "ACTIVE": 1, "WITHDRAWN": 2}
ROUTE_STATE = {"ABSENT": 0, "ACTIVE": 1, "SUSPENDED": 2}
FederationState = tuple[bool, int, int, int, bool]
FederationEdge = tuple[str, str, FederationState]


@dataclass(frozen=True)
class FederationRule:
    component_id: str
    operator: str
    kind: str
    pre_state: str | None
    post_state: str | None
    preserves_network: bool


def derive_federation_rules(root: Path = ROOT) -> tuple[FederationRule, ...]:
    subject = parse_network_manifests(root).by_name()["federation"]
    text = _source_text(root, subject)
    rules: list[FederationRule] = []
    for pair in subject.pairs:
        _, body = extract_operator(text, pair.formal_operator)
        require(
            "networkAfter=networkBefore" in body, f"{pair.formal_operator}: Network stutter missing"
        )
        if pair.formal_operator == "FederationGenesis":
            require(
                "EmptyFederationState(fs)" in body, "FederationGenesis empty-state guard missing"
            )
            require(
                r"federationId\inFederationIDs" in body,
                "FederationGenesis federation-id domain guard missing",
            )
            require(
                r"federationEpoch\inFederationEpochs" in body,
                "FederationGenesis epoch domain guard missing",
            )
            require(
                "!.federation_id=federationId" in body
                and "!.federation_epoch=federationEpoch" in body,
                "FederationGenesis identity update drift",
            )
            rules.append(
                FederationRule(pair.component_id, pair.formal_operator, "GENESIS", None, None, True)
            )
        elif pair.formal_operator == "MemberJoin":
            pre = re.search(r'fs\.members\[context\]="(ABSENT|ACTIVE|WITHDRAWN)"', body)
            post = re.search(r'!\.members\[context\]="(ABSENT|ACTIVE|WITHDRAWN)"', body)
            require(pre is not None and post is not None, "MemberJoin member-state clauses missing")
            require(
                "fs.federation_id#NoFederation" in body,
                "MemberJoin federation-exists guard missing",
            )
            require(r"context\inContexts" in body, "MemberJoin context domain guard missing")
            rules.append(
                FederationRule(
                    pair.component_id,
                    pair.formal_operator,
                    "JOIN",
                    pre.group(1),
                    post.group(1),
                    True,
                )
            )
        elif pair.formal_operator == "RouteGrant":
            member_values = re.findall(
                r'fs\.members\[(?:source|target)\]="(ABSENT|ACTIVE|WITHDRAWN)"', body
            )
            pre = re.search(r'fs\.routes\[route\]="(ABSENT|ACTIVE|SUSPENDED)"', body)
            post = re.search(r'!\.routes\[route\]="(ABSENT|ACTIVE|SUSPENDED)"', body)
            require(member_values == ["ACTIVE", "ACTIVE"], "RouteGrant active-member guards drift")
            require(
                r"source\inContexts" in body and r"target\inContexts" in body,
                "RouteGrant endpoint domain guards missing",
            )
            require("source#target" in body, "RouteGrant distinct-endpoint guard missing")
            require(pre is not None and post is not None, "RouteGrant route-state clauses missing")
            rules.append(
                FederationRule(
                    pair.component_id,
                    pair.formal_operator,
                    "GRANT",
                    pre.group(1),
                    post.group(1),
                    True,
                )
            )
        elif pair.formal_operator == "ExportArtifact":
            pre = re.search(r'fs\.routes\[route\]="(ABSENT|ACTIVE|SUSPENDED)"', body)
            require(pre is not None, "ExportArtifact route guard missing")
            require(
                r"source\inContexts" in body and r"target\inContexts" in body,
                "ExportArtifact endpoint domain guards missing",
            )
            require(r"artifact\inArtifacts" in body, "ExportArtifact artifact domain guard missing")
            require(
                "export\\notinfs.exports" in body,
                "ExportArtifact exact export-absence guard missing",
            )
            require("!.exports=@\\cup{export}" in body, "ExportArtifact add-export effect missing")
            rules.append(
                FederationRule(
                    pair.component_id, pair.formal_operator, "EXPORT", pre.group(1), None, True
                )
            )
        elif pair.formal_operator == "SuspendRoute":
            pre = re.search(r'fs\.routes\[route\]="(ABSENT|ACTIVE|SUSPENDED)"', body)
            post = re.search(r'!\.routes\[route\]="(ABSENT|ACTIVE|SUSPENDED)"', body)
            require(
                pre is not None and post is not None, "SuspendRoute route-state clauses missing"
            )
            require(
                r"source\inContexts" in body and r"target\inContexts" in body,
                "SuspendRoute endpoint domain guards missing",
            )
            rules.append(
                FederationRule(
                    pair.component_id,
                    pair.formal_operator,
                    "SUSPEND",
                    pre.group(1),
                    post.group(1),
                    True,
                )
            )
        elif pair.formal_operator == "MemberWithdraw":
            pre = re.search(r'fs\.members\[context\]="(ABSENT|ACTIVE|WITHDRAWN)"', body)
            post = re.search(r'!\.members\[context\]="(ABSENT|ACTIVE|WITHDRAWN)"', body)
            require(
                pre is not None and post is not None, "MemberWithdraw member-state clauses missing"
            )
            require(r"context\inContexts" in body, "MemberWithdraw context domain guard missing")
            require(
                'fs.routes[route]="ACTIVE"=>context\\notin{route[1],route[2]}' in body,
                "MemberWithdraw active-route exclusion drift",
            )
            rules.append(
                FederationRule(
                    pair.component_id,
                    pair.formal_operator,
                    "WITHDRAW",
                    pre.group(1),
                    post.group(1),
                    True,
                )
            )
        else:
            raise RelationalExpressionError(
                f"unsupported federation operator: {pair.formal_operator}"
            )
    return tuple(rules)


def federation_relational_edges_from_source(
    state: FederationState, root: Path = ROOT
) -> set[FederationEdge]:
    created, a, b, route, exported = state
    rules = {rule.kind: rule for rule in derive_federation_rules(root)}
    out: set[FederationEdge] = set()
    genesis = rules["GENESIS"]
    if not created:
        out.add((genesis.component_id, "-", (True, a, b, route, exported)))
    join = rules["JOIN"]
    for actor, index, value in (("A", 1, a), ("B", 2, b)):
        if created and value == MEMBER_STATE[join.pre_state or ""]:
            target = list(state)
            target[index] = MEMBER_STATE[join.post_state or ""]
            out.add((join.component_id, actor, tuple(target)))
    grant = rules["GRANT"]
    if (
        created
        and a == MEMBER_STATE["ACTIVE"]
        and b == MEMBER_STATE["ACTIVE"]
        and route == ROUTE_STATE[grant.pre_state or ""]
    ):
        out.add(
            (
                grant.component_id,
                "A-B",
                (created, a, b, ROUTE_STATE[grant.post_state or ""], exported),
            )
        )
    export_rule = rules["EXPORT"]
    if route == ROUTE_STATE[export_rule.pre_state or ""] and not exported:
        out.add((export_rule.component_id, "A-B", (created, a, b, route, True)))
    suspend = rules["SUSPEND"]
    if route == ROUTE_STATE[suspend.pre_state or ""]:
        out.add(
            (
                suspend.component_id,
                "A-B",
                (created, a, b, ROUTE_STATE[suspend.post_state or ""], exported),
            )
        )
    withdraw = rules["WITHDRAW"]
    for actor, index, value in (("A", 1, a), ("B", 2, b)):
        if value == MEMBER_STATE[withdraw.pre_state or ""] and route != ROUTE_STATE["ACTIVE"]:
            target = list(state)
            target[index] = MEMBER_STATE[withdraw.post_state or ""]
            out.add((withdraw.component_id, actor, tuple(target)))
    return out


def validate_federation_identity_guards(root: Path = ROOT) -> int:
    subject = parse_network_manifests(root).by_name()["federation"]
    text = _source_text(root, subject)
    expected = {
        "FederationGenesis": (
            r"federationId\inFederationIDs",
            r"federationEpoch\inFederationEpochs",
        ),
        "MemberJoin": (r"context\inContexts",),
        "RouteGrant": (r"source\inContexts", r"target\inContexts", "source#target"),
        "ExportArtifact": (r"source\inContexts", r"target\inContexts", r"artifact\inArtifacts"),
        "SuspendRoute": (r"source\inContexts", r"target\inContexts"),
        "MemberWithdraw": (r"context\inContexts",),
    }
    checks = 0
    for operator, markers in expected.items():
        _, body = extract_operator(text, operator)
        for marker in markers:
            require(marker in body, f"{operator}: identity/domain guard missing: {marker}")
            checks += 1
    return checks


def validate_all_relational_sources(root: Path = ROOT) -> int:
    derive_core_contract(root)
    derive_dynamic_contract(root)
    derive_liveness_contract(root)
    derive_composition_contract(root)
    rules = derive_federation_rules(root)
    validate_federation_identity_guards(root)
    count = 3 + 2 + 4 + 6 + len(rules)
    return count


def main() -> int:
    try:
        count = validate_all_relational_sources(ROOT)
        identity = validate_federation_identity_guards(ROOT)
        print(f"ALPHA4_NETWORK_RELATIONAL_SOURCE_DERIVATIONS={count}/{count} PASS")
        print(f"ALPHA4_FEDERATION_IDENTITY_GUARD_DERIVATIONS={identity}/{identity} PASS")
        print("ALPHA4_NETWORK_RELATIONAL_EXPRESSION=PASS")
        return 0
    except (RelationalExpressionError, OSError, UnicodeError, ValueError, KeyError) as error:
        print(f"ALPHA4_NETWORK_RELATIONAL_EXPRESSION_ERROR={error}")
        print("ALPHA4_NETWORK_RELATIONAL_EXPRESSION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
