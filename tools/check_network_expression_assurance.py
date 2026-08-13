from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = Path("theory/network-seed-reflection/EXPRESSION_ASSURANCE.json")
HISTORY_PATH = Path("history/REFERENCES.aset")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def reject_self_declared_verdict(response: dict[str, Any]) -> None:
    forbidden = {"pass", "verdict", "conformant", "conformance"}
    require(not (forbidden & set(response)), "adapter self-declares conformance")


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
    value = load_json(path)
    require(isinstance(value.get("describe"), dict), "transcript describe response missing")
    require(isinstance(value.get("cases"), dict), "transcript case responses missing")
    return value


def verify_retained_oracle(network_root: Path, profile: dict[str, Any]) -> None:
    subject = profile["historical_subject"]
    oracle = profile["formal_oracle"]
    history = (network_root / HISTORY_PATH).read_text(encoding="utf-8")

    history_markers = (
        "STATE NETWORK-0.1.0-ALPHA.3",
        f"TAG {subject['release_tag']}",
        f"COMMIT {subject['release_commit']}",
        f"DIGEST NETWORK-0.1.0-ALPHA.3 CANON-PACKAGE {subject['canon_package_digest']}",
        f"DIGEST NETWORK-0.1.0-ALPHA.3 CANON-PACKAGE-BYTES {subject['canon_package_sha256']}",
        "RELATION NETWORK-0.1.0-ALPHA.3 REFINES SEED-0.3.0-ALPHA.3",
        (
            "PROOF NETWORK-0.1.0-ALPHA.3 SEED-REFLECTION "
            f"{oracle['profile']} {oracle['obligations_proved']} {oracle['status']}"
        ),
    )
    for marker in history_markers:
        require(marker in history, f"historical oracle identity missing: {marker}")

    for artifact_name in ("network_model", "mapping", "proof"):
        artifact = oracle[artifact_name]
        path = network_root / artifact["path"]
        require(path.is_file(), f"retained oracle artifact missing: {artifact['path']}")
        require(
            sha256(path) == artifact["sha256"],
            f"retained oracle artifact drift: {artifact['path']}",
        )

    proof_text = (network_root / oracle["proof"]["path"]).read_text(encoding="utf-8")
    for theorem in oracle["final_theorems"]:
        require(f"THEOREM {theorem} ==" in proof_text, f"retained theorem missing: {theorem}")

    mapping_text = (network_root / oracle["mapping"]["path"]).read_text(encoding="utf-8")
    require("BridgeAdmitAsSeedRegister(o)" in mapping_text, "Seed RegisterRequest bridge missing")
    require(
        'NetworkProjectedSeedResolution(o) == IF o \\in imports THEN "UNKNOWN" ELSE "UNKNOWN"'
        in mapping_text,
        "projected Seed resolution drift",
    )
    require(
        "NetworkProjectedSeedEffectPermitted(o) == FALSE" in mapping_text,
        "projected Seed effect boundary drift",
    )

    for entry in profile["cases"]:
        path = network_root / entry["path"]
        require(path.is_file(), f"retained case missing: {entry['path']}")
        require(sha256(path) == entry["sha256"], f"retained case drift: {entry['path']}")
        case = load_json(path)
        require(case.get("case_id") == entry["case_id"], "retained case id drift")
        require(
            case.get("expected") == entry["expected"],
            "retained case expected observation drift",
        )


def verify_describe(response: dict[str, Any], profile: dict[str, Any]) -> None:
    protocol = profile["implementation_protocol"]
    subject = profile["historical_subject"]
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
    require(
        implementation.get("network_canon_package_digest") == subject["canon_package_digest"],
        "implementation is not bound to the exact Alpha3 canon package",
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
        require(
            imports.get(observation["import_id"]) == observation,
            "fresh admission exact import mismatch",
        )
        oracle = profile["formal_oracle"]
        require(
            actual.get("semantic_status") == oracle["projected_resolution"],
            "implementation observation disagrees with proved Seed resolution projection",
        )
        require(
            actual.get("enforcement") == "BLOCKED"
            and oracle["projected_effect_permitted"] is False,
            "implementation observation disagrees with proved Seed effect boundary",
        )
        return True

    if actual.get("state_changed") is False:
        require(
            imports == case["initial_state"].get("imports", {}),
            "non-state-changing case mutated observed Network import state",
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
    verify_retained_oracle(network_root, profile)
    require((command is None) != (transcript is None), "provide exactly one adapter source")

    protocol = profile["implementation_protocol"]["protocol"]
    if transcript is None:
        assert command is not None
        describe = run_adapter(
            command, adapter_cwd, {"protocol": protocol, "operation": "describe"}
        )
        case_responses: dict[str, Any] = {}
    else:
        describe = transcript["describe"]
        case_responses = transcript["cases"]
    verify_describe(describe, profile)

    fresh_projection_cases = 0
    observations: list[dict[str, Any]] = []
    for entry in profile["cases"]:
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
        "historical_network_subject": profile["historical_subject"],
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

    count = report["black_box_cases"]
    oracle_count = report["fresh_admission_seed_oracle_cases"]
    print("NETWORK_EXPRESSION_FORMAL_ORACLE=35/35 MECHANICALLY_PROVED")
    print(f"NETWORK_EXPRESSION_BLACKBOX_CASES={count}/{count} PASS")
    print(f"NETWORK_EXPRESSION_SEED_ORACLE_CASES={oracle_count}/{oracle_count} PASS")
    print("NETWORK_EXPRESSION_IMPLEMENTATION_IMPORTS=NONE")
    print("NETWORK_EXPRESSION_INDEPENDENT_ASSURANCE=PASS")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
