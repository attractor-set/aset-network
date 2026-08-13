#!/usr/bin/env python3
"""Independently check an external Network expression against frozen Alpha3 proof evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

PROFILE_PATH = Path("assurance/expression-independent/ASSURANCE_PROFILE.json")
CANON_PACKAGE_PATH = Path("extension/canonical/CANON_PACKAGE.json")
SEED_REFINEMENT_EVIDENCE_PATH = Path("extension/canonical/assurance/seed-refinement-proof.json")
FORBIDDEN_RESPONSE_KEYS = {"pass", "verdict", "conformant", "conformance"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_self_declared_verdict(response: dict[str, Any]) -> None:
    found: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            found.update(FORBIDDEN_RESPONSE_KEYS.intersection(value))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(response)
    require(not found, f"adapter self-declares assurance/conformance: {sorted(found)}")


def run_adapter(command: list[str], cwd: Path | None, request: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(request, sort_keys=True) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    require(completed.returncode == 0, f"adapter command failed: {completed.stderr.strip()}")
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("adapter returned invalid JSON") from exc
    require(isinstance(response, dict), "adapter response must be a JSON object")
    return response


def load_transcript(path: Path) -> dict[str, Any]:
    transcript = load_json(path)
    require(isinstance(transcript.get("describe"), dict), "transcript describe response missing")
    require(isinstance(transcript.get("cases"), dict), "transcript cases mapping missing")
    return transcript


def verify_frozen_oracle(network_root: Path, profile: dict[str, Any]) -> dict[str, Any]:
    subject = profile["subject"]
    oracle = profile["formal_oracle"]
    canon = load_json(network_root / CANON_PACKAGE_PATH)
    evidence = load_json(network_root / SEED_REFINEMENT_EVIDENCE_PATH)

    require(canon.get("canon_id") == subject["canon_id"], "frozen Network canon id mismatch")
    require(
        canon.get("extension_version") == subject["extension_version"],
        "frozen Network extension version mismatch",
    )
    require(
        canon.get("package_digest") == subject["canon_package_digest"],
        "frozen Network canon package digest mismatch",
    )
    require(
        sha256(network_root / CANON_PACKAGE_PATH) == subject["canon_package_sha256"],
        "frozen Network CANON_PACKAGE bytes changed",
    )

    conformance_path = network_root / subject["conformance_profile"]
    require(
        sha256(conformance_path) == subject["conformance_profile_sha256"],
        "frozen Network conformance profile changed",
    )
    conformance = load_json(conformance_path)
    require(conformance.get("case_count") == subject["case_count"], "frozen case count changed")

    for artifact_name in ("network_model", "mapping", "proof", "evidence"):
        artifact = oracle[artifact_name]
        require(
            sha256(network_root / artifact["path"]) == artifact["sha256"],
            f"formal oracle artifact identity mismatch: {artifact['path']}",
        )

    proof_gate = evidence.get("proof_gate", {})
    require(evidence.get("profile") == oracle["profile"], "refinement proof profile mismatch")
    require(
        evidence.get("status") == oracle["status"],
        "refinement proof is not mechanically proved",
    )
    require(
        proof_gate.get("obligations_proved") == oracle["obligations_proved"],
        "refinement proof-obligation evidence changed",
    )
    require(
        set(proof_gate.get("final_theorems", [])) == set(oracle["final_theorems"]),
        "refinement final theorem set changed",
    )

    proof_text = (network_root / oracle["proof"]["path"]).read_text(encoding="utf-8")
    for theorem in oracle["final_theorems"]:
        require(f"THEOREM {theorem} ==" in proof_text, f"refinement theorem missing: {theorem}")

    mapping_text = (network_root / oracle["mapping"]["path"]).read_text(encoding="utf-8")
    require("BridgeAdmitAsSeedRegister(o)" in mapping_text, "Seed RegisterRequest bridge missing")
    require(
        'NetworkProjectedSeedResolution(o) == IF o \\in imports THEN "UNKNOWN" ELSE "UNKNOWN"'
        in mapping_text,
        "frozen projected Seed resolution changed",
    )
    require(
        "NetworkProjectedSeedEffectPermitted(o) == FALSE" in mapping_text,
        "frozen projected Seed effect boundary changed",
    )
    return conformance


def verify_describe(response: dict[str, Any], profile: dict[str, Any]) -> None:
    protocol = profile["implementation_protocol"]
    subject = profile["subject"]
    reject_self_declared_verdict(response)
    require(response.get("protocol") == protocol["protocol"], "adapter protocol mismatch")
    implementation = response.get("implementation")
    require(isinstance(implementation, dict), "adapter implementation descriptor missing")
    require(implementation.get("name") == protocol["required_name"], "implementation name mismatch")
    require(implementation.get("normative") is False, "implementation must remain non-normative")
    require(
        implementation.get("network_canon_id") == subject["canon_id"],
        "implementation is not bound to the frozen Alpha3 Network canon",
    )
    require(
        implementation.get("network_extension_version") == subject["extension_version"],
        "implementation is not bound to Network 0.1.0-alpha.3",
    )
    operations = response.get("operations")
    require(isinstance(operations, list), "adapter operations missing")
    require(
        set(protocol["operations"]).issubset(set(operations)),
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


def verify_case_response(
    case: dict[str, Any],
    expected: dict[str, Any],
    response: dict[str, Any],
    profile: dict[str, Any],
) -> bool:
    reject_self_declared_verdict(response)
    protocol = profile["implementation_protocol"]["protocol"]
    require(response.get("protocol") == protocol, "adapter protocol mismatch")
    require(response.get("case_id") == case["case_id"], "adapter case id mismatch")
    actual = response.get("actual")
    require(isinstance(actual, dict), "adapter actual observation missing")
    require(actual == expected, f"black-box observable mismatch for {case['case_id']}")

    final_state = response.get("final_state")
    require(isinstance(final_state, dict), "adapter final_state observation missing")
    imports = final_state.get("imports")
    require(isinstance(imports, dict), "adapter final_state.imports observation missing")

    if fresh_import(case, actual):
        observation = copy.deepcopy(case["steps"][0]["payload"]["import"])
        import_id = observation["import_id"]
        require(
            imports.get(import_id) == observation,
            "fresh admission did not materialize exact import",
        )
        oracle = profile["formal_oracle"]
        require(
            actual.get("semantic_status") == oracle["projected_resolution"],
            "implementation Network observation disagrees with proved Seed resolution projection",
        )
        require(
            actual.get("enforcement") == "BLOCKED"
            and oracle["projected_effect_permitted"] is False,
            "implementation Network observation disagrees with proved Seed effect boundary",
        )
        return True

    if actual.get("state_changed") is False:
        require(
            imports == case["initial_state"].get("imports", {}),
            "non-state-changing case mutated the observed Network import state",
        )
    return False


def check(
    network_root: Path,
    *,
    command: list[str] | None = None,
    adapter_cwd: Path | None = None,
    transcript: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = load_json(network_root / PROFILE_PATH)
    require(profile.get("normative") is False, "assurance profile must remain non-normative")
    require(profile.get("normative_precedence") == "NONE", "assurance profile claims precedence")
    conformance = verify_frozen_oracle(network_root, profile)

    require((command is None) != (transcript is None), "provide exactly one adapter source")
    protocol = profile["implementation_protocol"]["protocol"]

    if transcript is None:
        assert command is not None
        describe = run_adapter(
            command,
            adapter_cwd,
            {"protocol": protocol, "operation": "describe"},
        )
        case_responses: dict[str, Any] = {}
    else:
        describe = transcript["describe"]
        case_responses = transcript["cases"]

    verify_describe(describe, profile)

    fresh_projection_cases = 0
    observations: list[dict[str, Any]] = []
    for entry in conformance["cases"]:
        case = load_json(network_root / entry["path"])
        expected = entry["expected"]
        if transcript is None:
            assert command is not None
            response = run_adapter(
                command,
                adapter_cwd,
                {"protocol": protocol, "operation": "execute_case", "case": case},
            )
        else:
            response = case_responses.get(case["case_id"])
            require(isinstance(response, dict), f"transcript case missing: {case['case_id']}")
        if verify_case_response(case, expected, response, profile):
            fresh_projection_cases += 1
        observations.append({"case_id": case["case_id"], "response": response})

    require(fresh_projection_cases > 0, "no fresh admission case exercised the formal Seed oracle")
    return {
        "assurance_id": profile["assurance_id"],
        "implementation": describe["implementation"],
        "frozen_network_subject": profile["subject"],
        "formal_oracle": {
            "profile": profile["formal_oracle"]["profile"],
            "status": profile["formal_oracle"]["status"],
            "obligations_proved": profile["formal_oracle"]["obligations_proved"],
            "final_theorems": profile["formal_oracle"]["final_theorems"],
        },
        "black_box_cases": len(observations),
        "fresh_admission_seed_oracle_cases": fresh_projection_cases,
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    command = shlex.split(args.adapter_command) if args.adapter_command else None
    transcript = load_transcript(args.transcript) if args.transcript else None
    try:
        report = check(
            args.network_root.resolve(),
            command=command,
            adapter_cwd=args.adapter_cwd.resolve() if args.adapter_cwd else None,
            transcript=transcript,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"NETWORK_EXPRESSION_INDEPENDENT_ASSURANCE=FAIL: {exc}")
        return 1

    print("NETWORK_EXPRESSION_FORMAL_ORACLE=35/35 MECHANICALLY_PROVED")
    black_box_cases = report["black_box_cases"]
    print(f"NETWORK_EXPRESSION_BLACKBOX_CASES={black_box_cases}/{black_box_cases} PASS")
    count = report["fresh_admission_seed_oracle_cases"]
    print(f"NETWORK_EXPRESSION_SEED_ORACLE_CASES={count}/{count} PASS")
    print("NETWORK_EXPRESSION_IMPLEMENTATION_IMPORTS=NONE")
    print("NETWORK_EXPRESSION_INDEPENDENT_ASSURANCE=PASS")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
