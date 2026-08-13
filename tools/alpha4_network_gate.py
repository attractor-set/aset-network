from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "-m", "tools.validate_alpha4_network"],
    [sys.executable, "-m", "tools.alpha4_network_paired_expression"],
    [sys.executable, "-m", "tools.alpha4_network_profiles_gate"],
    [sys.executable, "-m", "tools.alpha4_network_profile_paired_expression"],
]


def main() -> int:
    for command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            print("ALPHA4_NETWORK_GATE=FAIL")
            return result.returncode
    print("ALPHA4_NETWORK_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
