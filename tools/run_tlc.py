from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
DEFAULT_JAR = ROOT / ".tooling/tla2tools.jar"
META = ROOT / ".tooling/tlc"
MODELS = {
    "safety": ("NetworkExtensionTLC.tla", "NetworkExtensionTLC.cfg"),
    "admission-alias": ("NetworkAdmissionCore.tla", "NetworkAdmissionCore.cfg"),
    "history": ("NetworkHistory.tla", "NetworkHistory.cfg"),
    "legacy-safety": ("NetworkLegacyAlpha2.tla", "NetworkLegacyAlpha2.cfg"),
    "federation-liveness": (
        "NetworkLegacyAlpha2.tla",
        "NetworkLegacyAlpha2Liveness.cfg",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=[*MODELS, "all"], nargs="?", default="all")
    parser.add_argument("--jar", type=Path)
    args = parser.parse_args()
    jar = (args.jar or Path(os.environ.get("TLA2TOOLS_JAR", DEFAULT_JAR))).expanduser().resolve()

    if not jar.is_file():
        raise SystemExit(
            f"tla2tools.jar not found: {jar}; run python -m tools.bootstrap_tla "
            "or set TLA2TOOLS_JAR"
        )

    selected = list(MODELS) if args.model == "all" else [args.model]
    META.mkdir(parents=True, exist_ok=True)
    for name in selected:
        module, config = MODELS[name]
        model_dir = META / name
        if model_dir.exists():
            shutil.rmtree(model_dir)
        command = [
            "java",
            "-XX:+UseParallelGC",
            "-cp",
            str(jar),
            "tlc2.TLC",
            "-workers",
            "1",
            "-metadir",
            str(model_dir),
            "-config",
            config,
            module,
        ]
        print(f"TLC_MODEL={name.upper()}")
        result = subprocess.run(command, cwd=FORMAL, check=False)
        if result.returncode:
            print(f"TLC_{name.upper()}=FAIL")
            return result.returncode
        print(f"TLC_{name.upper()}=PASS")

    print("TLC_NETWORK_EXTENSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
