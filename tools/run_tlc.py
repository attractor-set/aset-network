from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
DEFAULT_JAR = ROOT / ".tooling/tla2tools.jar"
TLC_METADATA_ROOT = ROOT / ".tooling/tlc"

MODELS = {
    "safety": ("NetworkExtension.tla", "NetworkExtension.cfg"),
    "history": ("NetworkHistory.tla", "NetworkHistory.cfg"),
    "liveness": ("NetworkExtension.tla", "NetworkExtensionLiveness.cfg"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=[*MODELS, "all"], nargs="?", default="all")
    parser.add_argument("--jar", type=Path)
    args = parser.parse_args()

    jar = args.jar or Path(os.environ.get("TLA2TOOLS_JAR", DEFAULT_JAR))
    jar = jar.expanduser().resolve()
    if not jar.is_file():
        message = (
            f"tla2tools.jar not found: {jar}; "
            "run python tools/bootstrap_tla.py or set TLA2TOOLS_JAR"
        )
        raise SystemExit(message)

    selected = list(MODELS) if args.model == "all" else [args.model]
    TLC_METADATA_ROOT.mkdir(parents=True, exist_ok=True)
    for name in selected:
        module, config = MODELS[name]
        metadir = TLC_METADATA_ROOT / name
        if metadir.exists():
            shutil.rmtree(metadir)
        cmd = [
            "java",
            "-XX:+UseParallelGC",
            "-cp",
            str(jar),
            "tlc2.TLC",
            "-workers",
            "1",
            "-metadir",
            str(metadir),
            "-config",
            config,
            module,
        ]
        print(f"TLC_MODEL={name.upper()}")
        print(f"TLC_METADIR={metadir}")
        result = subprocess.run(cmd, cwd=FORMAL, check=False)
        if result.returncode != 0:
            print(f"TLC_{name.upper()}=FAIL")
            return result.returncode
        print(f"TLC_{name.upper()}=PASS")

    print("TLC_NETWORK_EXTENSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
