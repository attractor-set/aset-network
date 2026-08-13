from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
THEORY_ROOT = ROOT / "theory/network-seed-reflection"
NETWORK_MODEL = THEORY_ROOT / "formal/NetworkExtension.tla"
MAPPING = THEORY_ROOT / "formal/NetworkExtensionSeedRefinement.tla"
PROOF = THEORY_ROOT / "formal/NetworkExtensionSeedRefinementProofs.tla"
HISTORY = ROOT / "history/REFERENCES.aset"

ASSURANCE_ID = "ASET-NETWORK-ALPHA3-EXPRESSION-INDEPENDENT-ASSURANCE-V3"
PROOF_PROFILE = "ASET-NETWORK-SEED-REFLECTION-TLAPS-V3"
PROTOCOL = "ASET-NETWORK-EXPRESSION-BLACKBOX-V1"
FINAL_THEOREMS = (
    "NetworkExtensionRefinesSeedSafetySpec",
    "NetworkProjectionMatchesSeedResolution",
)
BRANCHES = (
    ("AdmitFresh", "FreshIdentifier"),
    ("AdmitReplay", "ExactReplay"),
    ("RejectConflict", "ConflictingIdentifier"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _quoted_set(text: str, name: str) -> set[str]:
    match = re.search(rf"^{re.escape(name)} == \{{(?P<body>[^}}]*)\}}$", text, re.MULTILINE)
    require(match is not None, f"theory set missing: {name}")
    return set(re.findall(r'"([A-Z0-9_]+)"', match.group("body")))


def _operator_body(text: str, name: str) -> str:
    match = re.search(
        (
            rf"^{re.escape(name)}\(o, result\) ==\n"
            r"(?P<body>.*?)(?=\n\n[A-Z][A-Za-z0-9_]*\(|\n\nNetworkAction ==)"
        ),
        text,
        re.MULTILINE | re.DOTALL,
    )
    require(match is not None, f"theory operator missing: {name}")
    return match.group("body")


def _branch_semantics(text: str, name: str, predicate: str) -> dict[str, Any]:
    body = _operator_body(text, name)
    require(predicate in body, f"{name} predicate drift")
    result = re.search(r'/\\ result = "([A-Z0-9_]+)"', body)
    require(result is not None, f"{name} result code missing")
    changed = "imports' = imports \\cup {o}" in body
    stutter = "UNCHANGED imports" in body
    require(changed != stutter, f"{name} state relation must be exactly change or stutter")

    return {
        "operator": name,
        "predicate": predicate,
        "code": result.group(1),
        "state_changed": changed,
    }


def _projection_literal(text: str, operator: str, literal: str) -> str:
    pattern = (
        rf"^{re.escape(operator)}\(result\) == IF result \\in ResultCodes "
        rf'THEN "(?P<value>[A-Z_]+)" ELSE "{re.escape(literal)}"$'
    )
    match = re.search(pattern, text, re.MULTILINE)
    require(match is not None, f"theory projection drift: {operator}")
    return match.group("value")


def _history_value(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    require(match is not None, f"historical identity missing: {label}")
    return match.group(1)


def historical_subject() -> dict[str, str]:
    text = HISTORY.read_text(encoding="utf-8")
    return {
        "canon_id": _history_value(
            r"^IDENTITY NETWORK-0\.1\.0-ALPHA\.3 CANON-ID (\S+)$", text, "Network canon id"
        ),
        "canon_package_digest": _history_value(
            r"^DIGEST NETWORK-0\.1\.0-ALPHA\.3 CANON-PACKAGE (sha256:[0-9a-f]{64})$",
            text,
            "Network canon package digest",
        ),
        "canon_package_sha256": _history_value(
            r"^DIGEST NETWORK-0\.1\.0-ALPHA\.3 CANON-PACKAGE-BYTES (sha256:[0-9a-f]{64})$",
            text,
            "Network canon package bytes",
        ),
        "extension_version": "0.1.0-alpha.3",
        "release_commit": _history_value(
            r"^COMMIT ([0-9a-f]{40})$",
            text.split("STATE SEED-0.3.0-ALPHA.3", 1)[0],
            "Network commit",
        ),
        "release_tag": _history_value(r"^TAG (v0\.1\.0-alpha\.3)$", text, "Network tag"),
    }


def seed_subject() -> dict[str, str]:
    text = HISTORY.read_text(encoding="utf-8")
    seed = text.split("STATE SEED-0.3.0-ALPHA.3", 1)[1]
    return {
        "release_commit": _history_value(r"^COMMIT ([0-9a-f]{40})$", seed, "Seed commit"),
        "release_tag": _history_value(r"^TAG (seed-0\.3\.0-alpha\.3)$", seed, "Seed tag"),
        "seed_resolution_path": "seed/canonical/formal/SeedResolution.tla",
        "seed_resolution_sha256": _history_value(
            r"^DIGEST SEED-0\.3\.0-ALPHA\.3 SEED-RESOLUTION-TLA (sha256:[0-9a-f]{64})$",
            seed,
            "SeedResolution digest",
        ),
    }


def theory_semantics() -> dict[str, Any]:
    text = NETWORK_MODEL.read_text(encoding="utf-8")
    result_codes = _quoted_set(text, "ResultCodes")
    accepted = _quoted_set(text, "AcceptedResults")
    branches = [_branch_semantics(text, name, predicate) for name, predicate in BRANCHES]
    branch_codes = {branch["code"] for branch in branches}
    require(branch_codes == result_codes, "branch results do not exhaust ResultCodes")
    require(accepted <= result_codes, "AcceptedResults escapes ResultCodes")

    require(
        {branch["operator"] for branch in branches} == {name for name, _ in BRANCHES},
        "branch drift",
    )
    require("\\/ AdmitFresh(o, result)" in text, "AdmitImport missing fresh branch")
    require("\\/ AdmitReplay(o, result)" in text, "AdmitImport missing replay branch")
    require("\\/ RejectConflict(o, result)" in text, "AdmitImport missing conflict branch")
    required_relations = (
        r"SameIdentifier(S, o) == {x \in S : x.import_id = o.import_id}",
        "FreshIdentifier(S, o) == SameIdentifier(S, o) = {}",
        r"ExactReplay(S, o) == o \in S",
        r"ConflictingIdentifier(S, o) == /\ SameIdentifier(S, o) # {}",
    )
    for relation in required_relations:
        require(relation in text, f"identifier relation drift: {relation}")
    require("import_id : ImportIDs" in text, "identifier surface missing from theory")
    return {
        "result_codes": sorted(result_codes),
        "accepted_results": sorted(accepted),
        "branches": branches,
        "projected_semantic_status": _projection_literal(
            text, "ProjectedResultStatus", "NOT_APPLICABLE"
        ),
        "projected_enforcement": _projection_literal(
            text, "ProjectedResultEnforcement", "NOT_APPLICABLE"
        ),
    }


def _import(import_id: str, evidence_digest: str) -> dict[str, Any]:
    return {
        "enforcement": "BLOCKED",
        "evidence_digest": evidence_digest,
        "import_id": import_id,
        "seed_scope": ["network/import"],
        "semantic_status": "UNKNOWN",
        "target_context_id": "ctx-A",
        "target_policy_epoch": 1,
        "target_state_root": "sha256:" + "a" * 64,
    }


def _expected(branch: dict[str, Any], semantics: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted": branch["code"] in semantics["accepted_results"],
        "code": branch["code"],
        "enforcement": semantics["projected_enforcement"],
        "semantic_status": semantics["projected_semantic_status"],
        "state_changed": branch["state_changed"],
    }


def _classify(imports: dict[str, dict[str, Any]], observation: dict[str, Any]) -> str:
    same_id = [item for item in imports.values() if item["import_id"] == observation["import_id"]]
    if not same_id:
        return "AdmitFresh"
    if observation in same_id:
        return "AdmitReplay"
    return "RejectConflict"


def generate_cases() -> list[dict[str, Any]]:
    semantics = theory_semantics()
    branches = {branch["operator"]: branch for branch in semantics["branches"]}
    first = _import("imp-001", "sha256:" + "1" * 64)
    second = _import("imp-002", "sha256:" + "2" * 64)
    conflict = _import("imp-001", "sha256:" + "3" * 64)
    history_digest = "sha256:" + "4" * 64

    definitions = (
        ("NET-POS-001", "positive", {}, [], first),
        ("NET-POS-002", "positive", {"imp-001": first}, [history_digest], first),
        ("NET-POS-003", "positive", {"imp-001": first}, [history_digest], second),
        ("NET-NEG-001", "negative", {"imp-001": first}, [history_digest], conflict),
    )
    cases: list[dict[str, Any]] = []
    for index, (case_id, polarity, imports, history, observation) in enumerate(definitions, 1):
        operator = _classify(imports, observation)
        branch = branches[operator]
        cases.append(
            {
                "case_id": case_id,
                "expected": _expected(branch, semantics),
                "initial_state": {
                    "history": copy.deepcopy(history),
                    "imports": copy.deepcopy(imports),
                },
                "polarity": polarity,
                "steps": [
                    {
                        "kind": "ADMIT_IMPORT",
                        "payload": {"import": copy.deepcopy(observation)},
                        "transition_id": f"generated-{index:03d}",
                    }
                ],
            }
        )
    return cases


def build_oracle() -> dict[str, Any]:
    semantics = theory_semantics()
    proof_text = PROOF.read_text(encoding="utf-8")
    mapping_text = MAPPING.read_text(encoding="utf-8")
    for theorem in FINAL_THEOREMS:
        require(f"THEOREM {theorem} ==" in proof_text, f"final theorem missing: {theorem}")
    for theorem in (
        "FreshRefinesSeedRegisterRequest",
        "ReplayRefinesSeedStutter",
        "ConflictRefinesSeedStutter",
    ):
        require(
            f"THEOREM {theorem} ==" in proof_text,
            f"branch refinement theorem missing: {theorem}",
        )
    require("BridgeFreshAsSeedRegister(o)" in mapping_text, "fresh Seed bridge missing")

    require(
        'NetworkProjectedSeedResolution(o) == "UNKNOWN"' in mapping_text,
        "Seed resolution projection drift",
    )

    require(
        "NetworkProjectedSeedEffectPermitted(o) == FALSE" in mapping_text,
        "Seed effect projection drift",
    )
    return {
        "assurance_id": ASSURANCE_ID,
        "document_type": "aset-network-generated-expression-independent-assurance-oracle",
        "schema_version": 3,
        "normative": False,
        "normative_precedence": "NONE",
        "historical_subject": historical_subject(),
        "formal_oracle": {
            "profile": PROOF_PROFILE,
            "network_model": {
                "path": NETWORK_MODEL.relative_to(ROOT).as_posix(),
                "sha256": sha256(NETWORK_MODEL),
            },
            "mapping": {"path": MAPPING.relative_to(ROOT).as_posix(), "sha256": sha256(MAPPING)},
            "proof": {"path": PROOF.relative_to(ROOT).as_posix(), "sha256": sha256(PROOF)},
            "seed_subject": seed_subject(),
            "final_theorems": list(FINAL_THEOREMS),
            "fresh_admission_seed_transition": "RegisterRequest",
            "replay_seed_transition": "STUTTER",
            "conflict_seed_transition": "STUTTER",
            "projected_resolution": "UNKNOWN",
            "projected_effect_permitted": False,
            "theory_semantics": semantics,
        },
        "implementation_protocol": {
            "protocol": PROTOCOL,
            "operations": ["describe", "execute_case"],
            "exact_historical_subject_required": True,
            "implementation_imports_forbidden": True,
            "self_declared_conformance_forbidden": True,
        },
        "cases": generate_cases(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    oracle = build_oracle()
    if args.output is not None:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(oracle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"NETWORK_SEED_REFLECTION_ORACLE={output.relative_to(ROOT)}")
    semantics = oracle["formal_oracle"]["theory_semantics"]
    print(f"NETWORK_SEED_REFLECTION_THEORY_BRANCHES={len(semantics['branches'])}/3 PASS")
    print(f"NETWORK_SEED_REFLECTION_GENERATED_CASES={len(oracle['cases'])}/4 PASS")
    print("NETWORK_SEED_REFLECTION_ORACLE_GENERATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
