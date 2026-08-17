from __future__ import annotations

import itertools
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "network/alpha4/profiles"

DYNAMIC_FORTH = PROFILES / "dynamic/operational/components.forth"
LIVENESS_FORTH = PROFILES / "liveness/operational/components.forth"
COMPOSITION_FORTH = PROFILES / "composition/federation-liveness/operational/components.forth"

EXPECTED_DYNAMIC_WORDS = {
    "PROFILE-APPLICABLE?": ("EXACT-PROFILE-BINDING?", "TARGET-LOCAL-ALLOW?", "AND"),
    "PROFILE-NETWORK-STUTTER?": ("SAME-NETWORK?",),
}
EXPECTED_LIVENESS_WORDS = {
    "EVENTUALLY-DELIVERED-CLAIM?": (
        "EVENTUAL-DELIVERY-FOR-RETAINED-EXPORT?",
        "NO-PERMANENT-TARGET-UNAVAILABILITY?",
        "AND",
    ),
    "EVENTUALLY-OBSERVED-CLAIM?": (
        "EVENTUAL-DELIVERY-FOR-RETAINED-EXPORT?",
        "EVENTUAL-TARGET-OBSERVATION?",
        "NO-PERMANENT-TARGET-UNAVAILABILITY?",
        "AND",
        "AND",
    ),
    "EVENTUALLY-RESOLVED-CLAIM?": (
        "EVENTUAL-DELIVERY-FOR-RETAINED-EXPORT?",
        "EVENTUAL-TARGET-OBSERVATION?",
        "TARGET-LOCAL-SEED-EVENTUAL-RESOLUTION?",
        "NO-PERMANENT-TARGET-UNAVAILABILITY?",
        "AND",
        "AND",
        "AND",
    ),
    "RESOLVED-RESULT-PERMITTED?": ("SEED-TERMINAL-RESULT?",),
}
EXPECTED_COMPOSITION_WORDS = {
    "REQUIRED-CAPABILITIES-SATISFIED?": (
        "LIVENESS-REQUIRED-CAPABILITIES",
        "SUBSET-OF?",
    ),
    "COMPOSITION-BOUNDARY-PRESERVED?": (
        "NO-PROFILE-PARENT?",
        "NO-STATE-TRANSFER?",
        "NO-TRANSITION-TRANSFER?",
        "NO-AUTHORITY-TRANSFER?",
        "AND",
        "AND",
        "AND",
    ),
    "DELIVERY-WITNESS?": ("EXPORTED?", "DELIVERED?", "AND"),
    "OBSERVATION-WITNESS?": ("DELIVERED?", "OBSERVED?", "AND"),
    "RESOLUTION-WITNESS?": ("OBSERVED?", "RESOLVED?", "AND"),
    "PROGRESS-WITNESS?": (
        "DELIVERY-WITNESS?",
        "OBSERVATION-WITNESS?",
        "RESOLUTION-WITNESS?",
        "AND",
        "AND",
    ),
}

EXPECTED_DYNAMIC_STACK_EFFECTS = {
    "PROFILE-APPLICABLE?": (("binding", "seed-binding", "recognition"), ("flag",)),
    "PROFILE-NETWORK-STUTTER?": (("network-before", "network-after"), ("flag",)),
}
EXPECTED_LIVENESS_STACK_EFFECTS = {
    "EVENTUALLY-DELIVERED-CLAIM?": (("assumptions",), ("flag",)),
    "EVENTUALLY-OBSERVED-CLAIM?": (("assumptions",), ("flag",)),
    "EVENTUALLY-RESOLVED-CLAIM?": (("assumptions",), ("flag",)),
    "RESOLVED-RESULT-PERMITTED?": (("result",), ("flag",)),
}
EXPECTED_COMPOSITION_STACK_EFFECTS = {
    "REQUIRED-CAPABILITIES-SATISFIED?": (("provided",), ("flag",)),
    "COMPOSITION-BOUNDARY-PRESERVED?": (
        ("parent", "state-xfer", "transition-xfer", "authority-xfer"),
        ("flag",),
    ),
    "DELIVERY-WITNESS?": (("exported", "delivered", "export"), ("flag",)),
    "OBSERVATION-WITNESS?": (("delivered", "observed", "export"), ("flag",)),
    "RESOLUTION-WITNESS?": (("observed", "resolved", "export"), ("flag",)),
    "PROGRESS-WITNESS?": (
        ("exported", "delivered", "observed", "resolved", "export"),
        ("flag",),
    ),
}

STACK_EFFECTS_BY_SOURCE = {
    DYNAMIC_FORTH: EXPECTED_DYNAMIC_STACK_EFFECTS,
    LIVENESS_FORTH: EXPECTED_LIVENESS_STACK_EFFECTS,
    COMPOSITION_FORTH: EXPECTED_COMPOSITION_STACK_EFFECTS,
}

LIVENESS_ASSUMPTIONS = {
    "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
    "EVENTUAL_TARGET_OBSERVATION",
    "TARGET_LOCAL_SEED_EVENTUAL_RESOLUTION",
    "NO_PERMANENT_TARGET_UNAVAILABILITY",
}
REQUIRED_CAPABILITIES = {"RETAINED_EXPORT", "DELIVERY", "TARGET_OBSERVATION"}
SEED_TERMINAL_RESULTS = {"ALLOW", "BLOCK"}


def _parse_operational_surface(
    path: Path,
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[tuple[str, ...], tuple[str, ...]]]]:
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
    return words, stacks


def parse_operational_words(path: Path) -> dict[str, tuple[str, ...]]:
    words, stacks = _parse_operational_surface(path)
    expected_stacks = STACK_EFFECTS_BY_SOURCE.get(path)
    if expected_stacks is not None and stacks != expected_stacks:
        raise RuntimeError(f"restricted operational stack contract mismatch for {path}: {stacks!r}")
    return words


def require_words(
    path: Path,
    expected: dict[str, tuple[str, ...]],
    expected_stacks: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] | None = None,
) -> None:
    words, stacks = _parse_operational_surface(path)
    if words != expected:
        raise RuntimeError(f"restricted operational vocabulary mismatch for {path}: {words!r}")
    stack_contract = expected_stacks or STACK_EFFECTS_BY_SOURCE.get(path)
    if stack_contract is None:
        raise RuntimeError(f"operational stack contract is not declared for {path}")
    if stacks != stack_contract:
        raise RuntimeError(f"restricted operational stack contract mismatch for {path}: {stacks!r}")


def _powerset(values: set[str]) -> list[set[str]]:
    ordered = sorted(values)
    return [
        set(item for item, included in zip(ordered, mask, strict=True) if included)
        for mask in itertools.product((False, True), repeat=len(ordered))
    ]


def dynamic_operational_applicable(exact_binding: bool, recognition: str) -> bool:
    return exact_binding and recognition == "ALLOW"


def dynamic_relational_applicable(exact_binding: bool, recognition: str) -> bool:
    return exact_binding and recognition == "ALLOW"


def dynamic_operational_stutter(before: str, after: str) -> bool:
    return before == after


def dynamic_relational_stutter(before: str, after: str) -> bool:
    return after == before


def bounded_dynamic_pairing_check() -> int:
    require_words(DYNAMIC_FORTH, EXPECTED_DYNAMIC_WORDS)
    checks = 0
    for exact_binding, recognition in itertools.product(
        (False, True), ("UNKNOWN", "ALLOW", "BLOCK")
    ):
        operational = dynamic_operational_applicable(exact_binding, recognition)
        relational = dynamic_relational_applicable(exact_binding, recognition)
        if operational != relational:
            raise RuntimeError("dynamic applicability pairing mismatch")
        checks += 1
    for before, after in itertools.product(("n0", "n1"), repeat=2):
        if dynamic_operational_stutter(before, after) != dynamic_relational_stutter(before, after):
            raise RuntimeError("dynamic Network-stutter pairing mismatch")
        checks += 1
    return checks


def liveness_operational_delivered(assumptions: set[str]) -> bool:
    return {
        "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
        "NO_PERMANENT_TARGET_UNAVAILABILITY",
    } <= assumptions


def liveness_relational_delivered(assumptions: set[str]) -> bool:
    return {
        "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
        "NO_PERMANENT_TARGET_UNAVAILABILITY",
    } <= assumptions


def liveness_operational_observed(assumptions: set[str]) -> bool:
    return {
        "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
        "EVENTUAL_TARGET_OBSERVATION",
        "NO_PERMANENT_TARGET_UNAVAILABILITY",
    } <= assumptions


def liveness_relational_observed(assumptions: set[str]) -> bool:
    return {
        "EVENTUAL_DELIVERY_FOR_RETAINED_EXPORT",
        "EVENTUAL_TARGET_OBSERVATION",
        "NO_PERMANENT_TARGET_UNAVAILABILITY",
    } <= assumptions


def liveness_operational_resolved(assumptions: set[str]) -> bool:
    return LIVENESS_ASSUMPTIONS <= assumptions


def liveness_relational_resolved(assumptions: set[str]) -> bool:
    return LIVENESS_ASSUMPTIONS <= assumptions


def liveness_operational_result_permitted(result: str) -> bool:
    return result in SEED_TERMINAL_RESULTS


def liveness_relational_result_permitted(result: str) -> bool:
    return result in SEED_TERMINAL_RESULTS


def bounded_liveness_pairing_check() -> int:
    require_words(LIVENESS_FORTH, EXPECTED_LIVENESS_WORDS)
    checks = 0
    for assumptions in _powerset(LIVENESS_ASSUMPTIONS):
        pairs = (
            (liveness_operational_delivered, liveness_relational_delivered),
            (liveness_operational_observed, liveness_relational_observed),
            (liveness_operational_resolved, liveness_relational_resolved),
        )
        for operational, relational in pairs:
            if operational(assumptions) != relational(assumptions):
                raise RuntimeError(f"liveness claim pairing mismatch: {assumptions!r}")
            checks += 1
    for result in ("UNKNOWN", "ALLOW", "BLOCK"):
        if liveness_operational_result_permitted(result) != liveness_relational_result_permitted(
            result
        ):
            raise RuntimeError(f"liveness terminal-result pairing mismatch: {result}")
        checks += 1
    return checks


def composition_operational_capabilities(provided: set[str]) -> bool:
    return REQUIRED_CAPABILITIES <= provided


def composition_relational_capabilities(provided: set[str]) -> bool:
    return REQUIRED_CAPABILITIES <= provided


def composition_operational_boundary(
    parent_relation: bool,
    state_transfer: bool,
    transition_transfer: bool,
    authority_transfer: bool,
) -> bool:
    return not any((parent_relation, state_transfer, transition_transfer, authority_transfer))


def composition_relational_boundary(
    parent_relation: bool,
    state_transfer: bool,
    transition_transfer: bool,
    authority_transfer: bool,
) -> bool:
    return (
        parent_relation is False
        and state_transfer is False
        and transition_transfer is False
        and authority_transfer is False
    )


def composition_operational_delivery_witness(
    exported: set[str], delivered: set[str], export: str
) -> bool:
    return export in exported and export in delivered


def composition_relational_delivery_witness(
    exported: set[str], delivered: set[str], export: str
) -> bool:
    return export in exported and export in delivered


def composition_operational_observation_witness(
    delivered: set[str], observed: set[str], export: str
) -> bool:
    return export in delivered and export in observed


def composition_relational_observation_witness(
    delivered: set[str], observed: set[str], export: str
) -> bool:
    return export in delivered and export in observed


def composition_operational_resolution_witness(
    observed: set[str], resolved: set[str], export: str
) -> bool:
    return export in observed and export in resolved


def composition_relational_resolution_witness(
    observed: set[str], resolved: set[str], export: str
) -> bool:
    return export in observed and export in resolved


def composition_operational_progress_witness(
    exported: set[str],
    delivered: set[str],
    observed: set[str],
    resolved: set[str],
    export: str,
) -> bool:
    return (
        composition_operational_delivery_witness(exported, delivered, export)
        and composition_operational_observation_witness(delivered, observed, export)
        and composition_operational_resolution_witness(observed, resolved, export)
    )


def composition_relational_progress_witness(
    exported: set[str],
    delivered: set[str],
    observed: set[str],
    resolved: set[str],
    export: str,
) -> bool:
    return (
        composition_relational_delivery_witness(exported, delivered, export)
        and composition_relational_observation_witness(delivered, observed, export)
        and composition_relational_resolution_witness(observed, resolved, export)
    )


def bounded_composition_pairing_check() -> int:
    require_words(COMPOSITION_FORTH, EXPECTED_COMPOSITION_WORDS)
    checks = 0
    for provided in _powerset(REQUIRED_CAPABILITIES):
        if composition_operational_capabilities(provided) != composition_relational_capabilities(
            provided
        ):
            raise RuntimeError(f"composition capability pairing mismatch: {provided!r}")
        checks += 1
    for values in itertools.product((False, True), repeat=4):
        if composition_operational_boundary(*values) != composition_relational_boundary(*values):
            raise RuntimeError(f"composition boundary pairing mismatch: {values!r}")
        checks += 1

    export = "e0"
    membership_sets = (set(), {export})
    for exported, delivered, observed, resolved in itertools.product(membership_sets, repeat=4):
        witness_pairs = (
            (
                composition_operational_delivery_witness(exported, delivered, export),
                composition_relational_delivery_witness(exported, delivered, export),
            ),
            (
                composition_operational_observation_witness(delivered, observed, export),
                composition_relational_observation_witness(delivered, observed, export),
            ),
            (
                composition_operational_resolution_witness(observed, resolved, export),
                composition_relational_resolution_witness(observed, resolved, export),
            ),
            (
                composition_operational_progress_witness(
                    exported, delivered, observed, resolved, export
                ),
                composition_relational_progress_witness(
                    exported, delivered, observed, resolved, export
                ),
            ),
        )
        for operational, relational in witness_pairs:
            if operational != relational:
                raise RuntimeError(
                    "composition finite progress-witness pairing mismatch: "
                    f"{(exported, delivered, observed, resolved)!r}"
                )
            checks += 1
    return checks


def main() -> int:
    dynamic = bounded_dynamic_pairing_check()
    liveness = bounded_liveness_pairing_check()
    composition = bounded_composition_pairing_check()
    total = dynamic + liveness + composition
    print("ALPHA4_DYNAMIC_OPERATIONAL_WORDS=2/2 PASS")
    print(f"ALPHA4_DYNAMIC_PAIRED_CASES={dynamic}/{dynamic} PASS")
    print("ALPHA4_LIVENESS_OPERATIONAL_WORDS=4/4 PASS")
    print(f"ALPHA4_LIVENESS_PAIRED_CASES={liveness}/{liveness} PASS")
    print("ALPHA4_FEDERATION_LIVENESS_OPERATIONAL_WORDS=6/6 PASS")
    print(f"ALPHA4_FEDERATION_LIVENESS_PAIRED_CASES={composition}/{composition} PASS")
    print(f"ALPHA4_PROFILE_OPERATIONAL_RELATIONAL_PAIRED_CASES={total}/{total} PASS")
    print("ALPHA4_NETWORK_PROFILE_PAIRED_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
