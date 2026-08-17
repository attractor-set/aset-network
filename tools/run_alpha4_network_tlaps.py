from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

try:
    from tools.alpha4_network_manifest import ProofBinding, parse_network_manifests
except ModuleNotFoundError:  # direct ``python tools/...py`` execution
    from alpha4_network_manifest import ProofBinding, parse_network_manifests

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "network/alpha4/formal"


def _run(tlapm: str, proof: ProofBinding) -> tuple[int, int | None, str]:
    result = subprocess.run(
        [tlapm, "-I", str(FORMAL), str(ROOT / proof.module)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout, end="")
    matches = re.findall(r"All ([0-9]+) obligations? proved\.", result.stdout)
    count = int(matches[-1]) if matches else None
    return result.returncode, count, result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    plan = parse_network_manifests(ROOT).by_name()["network"]
    total_expected = sum(item.expected_obligations for item in plan.proofs)
    total = 0
    for proof in plan.proofs:
        print(f"ALPHA4_NETWORK_TLAPS_PROOF={proof.proof_id}:START")
        print(f"ALPHA4_NETWORK_TLAPS_MODULE={proof.module}")
        print(f"ALPHA4_NETWORK_TLAPS_FINAL_THEOREM={proof.final_theorem}")
        print(f"ALPHA4_NETWORK_TLAPS_EXPECTED_OBLIGATIONS={proof.expected_obligations}")
        status, count, _ = _run(args.tlapm, proof)
        if status or count != proof.expected_obligations:
            print(
                f"ALPHA4_NETWORK_TLAPS_MODULE={Path(proof.module).name} "
                f"OBLIGATIONS={count} EXPECTED={proof.expected_obligations} SCOPE_DRIFT FAIL"
            )
            print("ALPHA4_NETWORK_TLAPS=FAIL")
            return status or 1
        total += count
        print(
            f"ALPHA4_NETWORK_TLAPS_MODULE={Path(proof.module).name} "
            f"OBLIGATIONS={count}/{proof.expected_obligations} PASS"
        )
    print(f"ALPHA4_NETWORK_TLAPS_OBLIGATIONS={total}/{total_expected} PASS")
    print("ALPHA4_NETWORK_TLAPS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
