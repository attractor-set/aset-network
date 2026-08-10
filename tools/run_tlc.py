from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_FORMAL = ROOT / "extension/canonical/formal"
FEDERATION_ASSURANCE = ROOT / "extension/canonical/profiles/federation/assurance"
FEDERATION_LIVENESS_COMPOSITION = (
    ROOT / "extension/canonical/assurance/profile-compositions/federation-liveness"
)
DEFAULT_JAR = ROOT / ".tooling/tla2tools.jar"
META = ROOT / ".tooling/tlc"
MODELS = {
    "safety": {
        "cwd": CORE_FORMAL,
        "module": "NetworkExtensionTLC.tla",
        "config": "NetworkExtensionTLC.cfg",
        "libraries": [],
    },
    "history": {
        "cwd": CORE_FORMAL,
        "module": "NetworkHistory.tla",
        "config": "NetworkHistory.cfg",
        "libraries": [],
    },
    "federation-profile": {
        "cwd": FEDERATION_ASSURANCE,
        "module": "FederationProfile.tla",
        "config": "FederationProfile.cfg",
        "libraries": [],
    },
    "federation-liveness": {
        "cwd": FEDERATION_LIVENESS_COMPOSITION,
        "module": "FederationCompositionLiveness.tla",
        "config": "FederationCompositionLiveness.cfg",
        "libraries": [FEDERATION_ASSURANCE],
    },
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
        model = MODELS[name]
        model_dir = META / name
        if model_dir.exists():
            shutil.rmtree(model_dir)
        command = ["java", "-XX:+UseParallelGC"]
        libraries = model["libraries"]
        if libraries:
            command.append("-DTLA-Library=" + os.pathsep.join(str(path) for path in libraries))
        command.extend(
            [
                "-cp",
                str(jar),
                "tlc2.TLC",
                "-workers",
                "1",
                "-metadir",
                str(model_dir),
                "-config",
                str(model["config"]),
                str(model["module"]),
            ]
        )
        print(f"TLC_MODEL={name.upper()}")
        result = subprocess.run(command, cwd=model["cwd"], check=False)
        if result.returncode:
            print(f"TLC_{name.upper()}=FAIL")
            return result.returncode
        print(f"TLC_{name.upper()}=PASS")

    print("TLC_NETWORK_EXTENSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
