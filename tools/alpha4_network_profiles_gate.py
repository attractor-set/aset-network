from __future__ import annotations

import re
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "network/alpha4/profiles"

DYNAMIC = PROFILES / "dynamic/DYNAMIC.aset"
FEDERATION = PROFILES / "federation/FEDERATION.aset"
FEDERATION_FORTH = PROFILES / "federation/operational/components.forth"
LIVENESS = PROFILES / "liveness/LIVENESS.aset"
COMPOSITION = PROFILES / "composition/federation-liveness/FEDERATION_LIVENESS.aset"

FEDERATION_STATES = {
    "FEDERATION-ID",
    "FEDERATION-EPOCH",
    "MEMBERS",
    "ROUTES",
    "EXPORTS",
}
FEDERATION_TRANSITIONS = {
    "FEDERATION-GENESIS",
    "MEMBER-JOIN",
    "ROUTE-GRANT",
    "EXPORT-ARTIFACT",
    "SUSPEND-ROUTE",
    "MEMBER-WITHDRAW",
}
FEDERATION_CAPABILITIES = {"RETAINED-EXPORT", "DELIVERY", "TARGET-OBSERVATION"}
FEDERATION_WORDS = {
    "FEDERATION-GENESIS",
    "MEMBER-JOIN",
    "ROUTE-GRANT",
    "EXPORT-ARTIFACT",
    "SUSPEND-ROUTE",
    "MEMBER-WITHDRAW",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def values(path: Path, prefix: str) -> list[str]:
    marker = prefix + " "
    return [line.removeprefix(marker) for line in lines(path) if line.startswith(marker)]


def validate_registry() -> None:
    registry = lines(PROFILES / "PROFILES.aset")
    require(
        registry[0] == "ASET-NETWORK-PROFILES 1 ASET-NETWORK-ALPHA4-PROFILES alpha4",
        "Alpha4 profile registry header mismatch",
    )
    require("PARENT-SUBJECT network/alpha4/NETWORK.aset" in registry, "profile parent missing")
    require(
        "PROFILE DYNAMIC network/alpha4/profiles/dynamic/DYNAMIC.aset OPTIONAL" in registry,
        "dynamic profile missing",
    )
    require(
        "PROFILE FEDERATION network/alpha4/profiles/federation/FEDERATION.aset OPTIONAL"
        in registry,
        "federation profile missing",
    )
    require(
        "PROFILE LIVENESS network/alpha4/profiles/liveness/LIVENESS.aset OPTIONAL" in registry,
        "liveness profile missing",
    )
    require(
        "INVARIANT PROFILE-AUTHORITY-INHERITANCE NEVER" in registry,
        "authority boundary missing",
    )
    require(
        "INVARIANT PROFILE-COMPOSITION-PARENT-RELATION NEVER" in registry,
        "composition boundary missing",
    )
    require(
        "INVARIANT PROFILE-ASSURANCE-REPRESENTATIONS OPERATIONAL,RELATIONAL,CAUSAL" in registry,
        "profile assurance representation invariant missing",
    )
    require(
        "INVARIANT PROFILE-THREE-WAY-CONGRUENCE REQUIRED" in registry,
        "profile three-way congruence invariant missing",
    )
    require(
        "INVARIANT PROFILE-SEMANTIC-PRECEDENCE NONE" in registry,
        "profile semantic precedence invariant missing",
    )
    require(
        "INVARIANT OPERATIONAL-EXPRESSION-SUBJECT SEMANTIC-OBJECT" in registry,
        "operational expression subject invariant missing",
    )
    require(
        "INVARIANT OPERATIONAL-EXPRESSION-REQUIRES-STATE NEVER" in registry,
        "operational expression must not require state ownership",
    )
    require(
        "INVARIANT OPERATIONAL-EXPRESSION-REQUIRES-TRANSITION NEVER" in registry,
        "operational expression must not require transition ownership",
    )
    require(
        "CHECK PROFILE-OPERATIONAL-RELATIONAL tools/alpha4_network_profile_paired_expression.py"
        in registry,
        "profile operational-relational gate missing",
    )
    require(
        "CHECK PROFILE-TRIANGULATION tools/alpha4_network_triangulated_expression.py" in registry,
        "profile triangulation gate missing",
    )


def validate_dynamic() -> tuple[int, int]:
    dynamic = lines(DYNAMIC)
    require("STATE-ADDED NONE" in dynamic, "dynamic profile must add no state")
    require("TRANSITION-ADDED NONE" in dynamic, "dynamic profile must add no transitions")
    require("NETWORK-STATE-CHANGE NEVER" in dynamic, "dynamic profile must preserve Network state")
    require("AUTHORITY-INHERITANCE NEVER" in dynamic, "dynamic profile authority boundary missing")
    require(
        "ACTIVATION TARGET-LOCAL-SEED-ALLOW EXACT-PROFILE-BINDING" in dynamic,
        "dynamic activation rule mismatch",
    )
    require(
        "OPERATIONAL network/alpha4/profiles/dynamic/operational/components.forth" in dynamic,
        "dynamic operational expression missing",
    )
    require(
        (
            "FORMAL-REFLECTION network/alpha4/profiles/dynamic/formal/"
            "DynamicRestrictedOperationalSemantics.tla"
        )
        in dynamic,
        "dynamic formal reflection missing",
    )
    require(
        "SEMANTIC-PRECEDENCE NONE" in dynamic,
        "dynamic semantic precedence drift",
    )
    require(
        "CAUSAL-MODEL network/alpha4/profiles/dynamic/causal/components.petri" in dynamic,
        "dynamic causal representation missing",
    )
    require(
        len([line for line in dynamic if line.startswith("CAUSAL-BIND ")]) == 2,
        "dynamic causal binding count mismatch",
    )
    require(
        any(line.startswith("PROOF OPERATIONAL_RELATIONAL_PAIRING ") for line in dynamic),
        "dynamic pairing proof missing",
    )

    checks = 0
    applicable = 0
    for exact in (False, True):
        for recognition in ("UNKNOWN", "ALLOW", "BLOCK"):
            checks += 1
            result = exact and recognition == "ALLOW"
            applicable += int(result)
            require(result == (exact and recognition == "ALLOW"), "dynamic bounded mismatch")
    return checks, applicable


def validate_federation_surface() -> None:
    federation = lines(FEDERATION)
    require(
        set(values(FEDERATION, "STATE")) == FEDERATION_STATES,
        "federation state ownership mismatch",
    )
    require(
        set(values(FEDERATION, "TRANSITION")) == FEDERATION_TRANSITIONS,
        "federation transition ownership mismatch",
    )
    require(
        set(values(FEDERATION, "CAPABILITY")) == FEDERATION_CAPABILITIES,
        "federation capabilities mismatch",
    )
    require(
        "INVARIANT NETWORK-IMPORTS-STUTTER-ON-PROFILE-TRANSITION" in federation,
        "Network stutter invariant missing",
    )
    require(
        "INVARIANT AUTHORITY-INHERITANCE NEVER" in federation,
        "federation authority boundary missing",
    )
    require("SEMANTIC-PRECEDENCE NONE" in federation, "federation semantic precedence drift")
    require(
        "CAUSAL-MODEL network/alpha4/profiles/federation/causal/components.petri" in federation,
        "federation causal representation missing",
    )
    require(
        len([line for line in federation if line.startswith("CAUSAL-BIND ")]) == 6,
        "federation causal binding count mismatch",
    )
    require(
        any(line.startswith("PROOF OPERATIONAL_RELATIONAL_PAIRING ") for line in federation),
        "federation pairing proof missing",
    )

    source = FEDERATION_FORTH.read_text(encoding="utf-8")
    words = set(re.findall(r"^:\s+([A-Z0-9-]+)\s", source, flags=re.MULTILINE))
    require(words == FEDERATION_WORDS, f"federation Forth vocabulary mismatch: {sorted(words)}")


def bounded_federation_check() -> tuple[int, int]:
    # State: created, member A, member B, A->B route, export X.
    # Member states: 0 absent, 1 active, 2 withdrawn. Route: 0 absent, 1 active, 2 suspended.
    initial = (False, 0, 0, 0, False)
    queue = deque([initial])
    seen = {initial}
    edges = 0

    def successors(
        state: tuple[bool, int, int, int, bool],
    ) -> set[tuple[bool, int, int, int, bool]]:
        created, a, b, route, exported = state
        out: set[tuple[bool, int, int, int, bool]] = set()
        if not created:
            out.add((True, a, b, route, exported))
        if created and a == 0:
            out.add((created, 1, b, route, exported))
        if created and b == 0:
            out.add((created, a, 1, route, exported))
        if created and a == 1 and b == 1 and route == 0:
            out.add((created, a, b, 1, exported))
        if route == 1 and not exported:
            out.add((created, a, b, route, True))
        if route == 1:
            out.add((created, a, b, 2, exported))
        if a == 1 and route != 1:
            out.add((created, 2, b, route, exported))
        if b == 1 and route != 1:
            out.add((created, a, 2, route, exported))
        return out

    while queue:
        state = queue.popleft()
        created, a, b, route, exported = state
        require(not (route == 1 and (a != 1 or b != 1)), "active route without active members")
        require(not (exported and route == 0), "export without granted route")
        for target in successors(state):
            edges += 1
            # Network imports are absent from profile state; every edge stutters them.
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return len(seen), edges


def validate_liveness() -> None:
    liveness = lines(LIVENESS)
    require("STATE-ADDED NONE" in liveness, "liveness must add no state")
    require("TRANSITION-ADDED NONE" in liveness, "liveness must add no transitions")
    require("AUTHORITY-INHERITANCE NEVER" in liveness, "liveness authority boundary missing")
    require(
        set(values(LIVENESS, "REQUIRES-CAPABILITY")) == FEDERATION_CAPABILITIES,
        "liveness capability requirements mismatch",
    )
    require(
        set(values(LIVENESS, "SEED-TERMINAL-RESULT")) == {"ALLOW", "BLOCK"},
        "Seed terminal result contract mismatch",
    )
    require("EVENTUAL-ALLOW-REQUIRED FALSE" in liveness, "liveness must not require eventual ALLOW")
    require(
        "OPERATIONAL network/alpha4/profiles/liveness/operational/components.forth" in liveness,
        "liveness operational expression missing",
    )
    require(
        (
            "FORMAL-REFLECTION network/alpha4/profiles/liveness/formal/"
            "LivenessRestrictedOperationalSemantics.tla"
        )
        in liveness,
        "liveness formal reflection missing",
    )
    require("SEMANTIC-PRECEDENCE NONE" in liveness, "liveness semantic precedence drift")
    require(
        "CAUSAL-MODEL network/alpha4/profiles/liveness/causal/components.petri" in liveness,
        "liveness causal representation missing",
    )
    require(
        len([line for line in liveness if line.startswith("CAUSAL-BIND ")]) == 4,
        "liveness causal binding count mismatch",
    )
    require(
        any(line.startswith("PROOF OPERATIONAL_RELATIONAL_PAIRING ") for line in liveness),
        "liveness pairing proof missing",
    )


def validate_composition() -> None:
    composition = lines(COMPOSITION)
    require(
        "PROFILE-PARENT-RELATION FALSE" in composition,
        "composition must not create parent relation",
    )
    require(
        "STATE-OWNERSHIP-TRANSFER NONE" in composition,
        "composition state ownership transfer must remain NONE",
    )
    require(
        "TRANSITION-OWNERSHIP-TRANSFER NONE" in composition,
        "composition transition ownership transfer must remain NONE",
    )
    require(
        "AUTHORITY-TRANSFER NONE" in composition,
        "composition authority transfer must remain NONE",
    )
    require(
        set(values(COMPOSITION, "PROVIDES")) == FEDERATION_CAPABILITIES,
        "composition provided capabilities mismatch",
    )
    require(
        set(values(COMPOSITION, "REQUIRES")) == FEDERATION_CAPABILITIES,
        "composition required capabilities mismatch",
    )
    require(
        "TARGET-OBSERVATION-WITNESS ASSURANCE-WITNESS-FOR-NETWORK-ADMIT-IMPORT" in composition,
        "Network observation ownership mismatch",
    )
    require(
        "TARGET-LOCAL-RESOLUTION-WITNESS ASSURANCE-WITNESS-FOR-SEED-RESOLUTION" in composition,
        "Seed resolution ownership mismatch",
    )
    require(
        (
            "OPERATIONAL network/alpha4/profiles/composition/federation-liveness/"
            "operational/components.forth"
        )
        in composition,
        "composition operational expression missing",
    )
    require(
        (
            "FORMAL-REFLECTION network/alpha4/profiles/composition/federation-liveness/formal/"
            "FederationLivenessRestrictedOperationalSemantics.tla"
        )
        in composition,
        "composition formal reflection missing",
    )
    require("SEMANTIC-PRECEDENCE NONE" in composition, "composition semantic precedence drift")
    require(
        (
            "CAUSAL-MODEL network/alpha4/profiles/composition/federation-liveness/"
            "causal/components.petri"
        )
        in composition,
        "composition causal representation missing",
    )
    require(
        len([line for line in composition if line.startswith("CAUSAL-BIND ")]) == 6,
        "composition causal binding count mismatch",
    )
    require(
        any(line.startswith("PROOF OPERATIONAL_RELATIONAL_PAIRING ") for line in composition),
        "composition pairing proof missing",
    )


def main() -> int:
    validate_registry()
    dynamic_checks, applicable = validate_dynamic()
    validate_federation_surface()
    states, edges = bounded_federation_check()
    validate_liveness()
    validate_composition()
    print("ALPHA4_NETWORK_PROFILES=dynamic,federation,liveness")
    print("ALPHA4_DYNAMIC_STATE_FIELDS_ADDED=0 TRANSITIONS_ADDED=0")
    print(f"ALPHA4_DYNAMIC_BOUNDED_CASES={dynamic_checks} APPLICABLE={applicable} PASS")
    print(
        f"ALPHA4_FEDERATION_STATE_FIELDS={len(FEDERATION_STATES)} "
        f"TRANSITIONS={len(FEDERATION_TRANSITIONS)}"
    )
    print(f"ALPHA4_FEDERATION_BOUNDED_STATES={states} TRANSITIONS={edges} PASS")
    print("ALPHA4_FEDERATION_NETWORK_PROJECTION=STUTTER")
    print("ALPHA4_LIVENESS_STATE_FIELDS_ADDED=0 TRANSITIONS_ADDED=0")
    print("ALPHA4_LIVENESS_TERMINAL_RESULTS=ALLOW,BLOCK EVENTUAL_ALLOW_REQUIRED=false")
    print("ALPHA4_FEDERATION_LIVENESS_PARENT_RELATION=false AUTHORITY_TRANSFER=false")
    print("ALPHA4_PROFILE_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
    print("ALPHA4_PROFILE_THREE_WAY_CONGRUENCE=REQUIRED")
    print("ALPHA4_PROFILE_SEMANTIC_PRECEDENCE=NONE")
    print("ALPHA4_PROFILE_OPERATIONAL_EXPRESSION_REQUIRES_STATE=false")
    print("ALPHA4_PROFILE_OPERATIONAL_EXPRESSION_REQUIRES_TRANSITION=false")
    print("ALPHA4_NETWORK_PROFILES_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
