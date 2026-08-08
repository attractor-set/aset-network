from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / ".tooling/tla2tools.jar"
VERSION = "1.7.4"
URL = f"https://github.com/tlaplus/tlaplus/releases/download/v{VERSION}/tla2tools.jar"
SHA1 = "bee4a54f3ee3d4afc347c3240ec2d9e93b075104"


def digest(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()  # noqa: S324 - upstream publishes SHA-1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.is_file() and digest(output) == SHA1:
        print(f"TLA_TOOLS_VERSION={VERSION}")
        print(f"TLA_TOOLS={output}")
        print("TLA_TOOLS_BOOTSTRAP=PASS_CACHED")
        return 0

    with urllib.request.urlopen(URL, timeout=60) as response:  # noqa: S310 - pinned HTTPS URL
        data = response.read()
    actual = hashlib.sha1(data).hexdigest()  # noqa: S324 - verify published upstream checksum
    if actual != SHA1:
        raise SystemExit(f"tla2tools checksum mismatch: {actual}")
    output.write_bytes(data)
    print(f"TLA_TOOLS_VERSION={VERSION}")
    print(f"TLA_TOOLS={output}")
    print("TLA_TOOLS_BOOTSTRAP=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
