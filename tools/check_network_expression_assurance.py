from __future__ import annotations

import argparse
import copy
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from tools.network_seed_reflection_oracle import PROTOCOL, build_oracle

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_self_declared_verdict(response: dict[str, Any]) -> None:
    reserved_verdict_fields = {"pass", "verdict", "conformant", "conformance"}
    require(
        not (reserved_verdict_fields & set(response)),
        "adapter must not self-declare conformance",
    )


def run_adapter(command: list[str], cwd: Path | None, request: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(request, sort_keys=True) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    require(result.returncode == 0, f"adapter failed: {result.stderr.strip()}")
    response = json.loads(result.stdout)
    require(isinstance(response, dict), "adapter response must be a JSON object")
    return response


def load_transcript(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "transcript must be a JSON object")
    require(isinstance(value.get("describe"), dict), "transcript describe response missing")
    require(isinstance(value.get("cases"), dict), "transcript case responses missing")
    return value


def load_proof_evidence(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "proof evidence must be a JSON object")
    return value


def verify_proof_evidence(oracle: dict[str, Any], evidence: dict[str, Any]) -> None:
    formal = oracle["formal_oracle"]
    require(evidence.get("verdict") == "PASS", "reflection proof evidence is not PASS")
    require(evidence.get("profile") == formal["profile"], "reflection proof profile mismatch")
    require(
        evidence.get("seed_release_commit") == formal["seed_subject"]["release_commit"],
        "reflection proof Seed commit mismatch",
    )
    require(
        evidence.get("seed_resolution_sha256") == formal["seed_subject"]["seed_resolution_sha256"],
        "reflection proof SeedResolution identity mismatch",
    )
    identities = evidence.get("theory_sha256")
    require(isinstance(identities, dict), "reflection proof theory identity missing")
    for key in ("network_model", "mapping", "proof"):
        require(
            identities.get(key) == formal[key]["sha256"],
            f"reflection proof {key} identity mismatch",
        )
    obligations = evidence.get("obligations_proved")

    require(
        isinstance(obligations, int) and obligations > 0,
        "reflection proof obligation count missing",
    )
    require(
        evidence.get("final_theorems") == formal["final_theorems"],
        "reflection proof final theorem set mismatch",
    )


def verify_describe(response: dict[str, Any], oracle: dict[str, Any]) -> None:
    subject = oracle["historical_subject"]
    reject_self_declared_verdict(response)
    require(response.get("protocol") == PROTOCOL, "adapter protocol mismatch")
    implementation = response.get("implementation")
    require(isinstance(implementation, dict), "adapter implementation descriptor missing")

    require(
        isinstance(implementation.get("name"), str) and implementation["name"],
        "implementation name missing",
    )
    require(implementation.get("normative") is False, "implementation must remain non-normative")
    require(
        implementation.get("network_canon_id") == subject["canon_id"],
        "implementation is not bound to the frozen Alpha3 Network canon",
    )
    require(
        implementation.get("network_extension_version") == subject["extension_version"],
        "implementation is not bound to Network 0.1.0-alpha.3",
    )
    require(
        implementation.get("network_canon_package_digest") == subject["canon_package_digest"],
        "implementation is not bound to the exact Alpha3 canon package",
    )
    operations = response.get("operations")
    require(isinstance(operations, list), "adapter operations missing")

    require(
        {"describe", "execute_case"}.issubset(set(operations)),
        "required adapter operations missing",
    )


def fresh_import(case: dict[str, Any], actual: dict[str, Any]) -> bool:
    return (
        actual.get("accepted") is True
        and actual.get("code") == "IMPORT_ADMITTED"
        and actual.get("state_changed") is True
        and len(case.get("steps", [])) == 1
        and case["steps"][0].get("kind") == "ADMIT_IMPORT"
    )


def stutter_case(actual: dict[str, Any]) -> bool:
    return (
        actual.get("code") in {"IDEMPOTENT_REPLAY", "IDENTIFIER_CONFLICT"}
        and actual.get("state_changed") is False
    )


def verify_case_response(
    case: dict[str, Any],
    response: dict[str, Any],
    oracle: dict[str, Any],
) -> tuple[bool, bool]:
    reject_self_declared_verdict(response)
    require(response.get("protocol") == PROTOCOL, "adapter protocol mismatch")
    require(response.get("case_id") == case["case_id"], "adapter case id mismatch")
    actual = response.get("actual")
    require(isinstance(actual, dict), "adapter actual observation missing")
    expected = case["expected"]
    require(actual == expected, f"black-box observable mismatch for {case['case_id']}")

    final_state = response.get("final_state")
    require(isinstance(final_state, dict), "adapter final_state observation missing")
    imports = final_state.get("imports")
    require(isinstance(imports, dict), "adapter final_state.imports observation missing")

    formal = oracle["formal_oracle"]
    if fresh_import(case, actual):
        observation = copy.deepcopy(case["steps"][0]["payload"]["import"])

        require(
            imports.get(observation["import_id"]) == observation,
            "fresh admission exact import mismatch",
        )
        require(
            actual.get("semantic_status") == formal["projected_resolution"],
            "implementation observation disagrees with proved Seed resolution projection",
        )
        require(
            actual.get("enforcement") == "BLOCKED"
            and formal["projected_effect_permitted"] is False,
            "implementation observation disagrees with proved Seed effect boundary",
        )
        return True, False

    if stutter_case(actual):
        require(
            imports == case["initial_state"].get("imports", {}),
            "replay/conflict changed observed Network import state",
        )
        require(
            actual.get("semantic_status") == formal["projected_resolution"],
            "stutter observation disagrees with proved Seed resolution projection",
        )
        require(
            actual.get("enforcement") == "BLOCKED"
            and formal["projected_effect_permitted"] is False,
            "stutter observation disagrees with proved Seed effect boundary",
        )
        return False, True

    raise ValueError(f"generated theory case is not classified: {case['case_id']}")


def check(
    network_root: Path,
    *,
    command: list[str] | None = None,
    adapter_cwd: Path | None = None,
    transcript: dict[str, Any] | None = None,
    proof_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:

    require(
        network_root.resolve() == ROOT.resolve(),
        "checker must run against this repository theory",
    )
    oracle = build_oracle()

    require(
        oracle.get("normative") is False,
        "generated assurance oracle must remain non-normative",
    )
    require(oracle.get("normative_precedence") == "NONE", "generated oracle claims precedence")
    require((command is None) != (transcript is None), "provide exactly one adapter source")
    if proof_evidence is not None:
        verify_proof_evidence(oracle, proof_evidence)

    if transcript is None:
        assert command is not None

        describe = run_adapter(
            command,
            adapter_cwd,
            {"protocol": PROTOCOL, "operation": "describe"},
        )
        case_responses: dict[str, Any] = {}
    else:
        describe = transcript["describe"]
        case_responses = transcript["cases"]
    verify_describe(describe, oracle)

    fresh_cases = 0
    stutter_cases = 0
    observations: list[dict[str, Any]] = []
    for case in oracle["cases"]:
        if transcript is None:
            assert command is not None
            response = run_adapter(
                command,
                adapter_cwd,
                {"protocol": PROTOCOL, "operation": "execute_case", "case": case},
            )
        else:
            response = case_responses.get(case["case_id"])
            require(isinstance(response, dict), f"transcript case missing: {case['case_id']}")
        fresh, stutter = verify_case_response(case, response, oracle)
        fresh_cases += int(fresh)
        stutter_cases += int(stutter)
        observations.append({"case_id": case["case_id"], "response": response})

    require(fresh_cases == 2, "generated oracle did not exercise both fresh-admission witnesses")

    require(
        stutter_cases == 2,
        "generated oracle did not exercise replay and conflict stutter witnesses",
    )
    return {
        "assurance_id": oracle["assurance_id"],
        "implementation": describe["implementation"],
        "historical_network_subject": oracle["historical_subject"],
        "formal_oracle": {
            "profile": oracle["formal_oracle"]["profile"],
            "proof_evidence_verified": proof_evidence is not None,
            "final_theorems": oracle["formal_oracle"]["final_theorems"],
            "theory_sha256": {
                key: oracle["formal_oracle"][key]["sha256"]
                for key in ("network_model", "mapping", "proof")
            },
        },
        "black_box_cases": len(observations),
        "fresh_admission_seed_register_cases": fresh_cases,
        "replay_conflict_seed_stutter_cases": stutter_cases,
        "observations": observations,
        "verdict": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network-root", type=Path, default=Path.cwd())
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--adapter-command")
    source.add_argument("--transcript", type=Path)
    parser.add_argument("--adapter-cwd", type=Path)
    parser.add_argument("--proof-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    command = shlex.split(args.adapter_command) if args.adapter_command else None
    transcript = load_transcript(args.transcript) if args.transcript else None
    proof_evidence = load_proof_evidence(args.proof_evidence)
    try:
        report = check(
            args.network_root.resolve(),
            command=command,
            adapter_cwd=args.adapter_cwd.resolve() if args.adapter_cwd else None,
            transcript=transcript,
            proof_evidence=proof_evidence,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"NETWORK_EXPRESSION_INDEPENDENT_ASSURANCE=FAIL: {exc}")
        return 1

    count = report["black_box_cases"]
    fresh = report["fresh_admission_seed_register_cases"]
    stutter = report["replay_conflict_seed_stutter_cases"]
    print("NETWORK_EXPRESSION_FORMAL_ORACLE=GENERATED_FROM_THEORY PROOF_EVIDENCE=PASS")
    print(f"NETWORK_EXPRESSION_BLACKBOX_CASES={count}/{count} PASS")
    print(f"NETWORK_EXPRESSION_SEED_REGISTER_CASES={fresh}/{fresh} PASS")
    print(f"NETWORK_EXPRESSION_SEED_STUTTER_CASES={stutter}/{stutter} PASS")
    print("NETWORK_EXPRESSION_IMPLEMENTATION_IMPORTS=NONE")
    print("NETWORK_EXPRESSION_INDEPENDENT_ASSURANCE=PASS")
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
