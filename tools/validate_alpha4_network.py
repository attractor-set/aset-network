from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "network/alpha4/NETWORK.aset"
BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_binding() -> dict[str, str]:
    lines = [
        line.strip() for line in BINDING.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    require(
        lines[0] == "ASET-SEED-BINDING 1 ASET-SEED-0.4-ALPHA CONTENT-ADDRESSED",
        "Seed Alpha4 binding header mismatch",
    )
    sources: dict[str, str] = {}
    for line in lines:
        if line.startswith("SOURCE "):
            _, path, digest = line.split()
            require(path not in sources, f"duplicate bound source: {path}")
            require(re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None, "bad digest")
            sources[path] = digest
    require(len(sources) == 8, "Seed Alpha4 binding must cover exactly 8 semantic sources")
    require(
        "REQUIRED-SEED-PAIR ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN "
        "ObserveUnknown ObserveUnknownPairing" in lines,
        "Seed OBSERVE-UNKNOWN pairing requirement missing",
    )
    require(
        "NETWORK-PROJECTION ADMIT-IMPORT OBSERVE-UNKNOWN" in lines,
        "Network-to-Seed projection declaration missing",
    )
    return sources


def validate_seed_root(seed_root: Path, sources: dict[str, str]) -> None:
    for relative, expected in sources.items():
        path = seed_root / relative
        require(path.is_file(), f"bound Seed source missing: {relative}")
        require(sha256(path) == expected, f"bound Seed source digest mismatch: {relative}")
    seed = (seed_root / "seed/alpha4/SEED.aset").read_text(encoding="utf-8")
    require(
        seed.startswith("ASET-SEED 1 ASET-SEED-0.4-ALPHA 0.4alpha\n"),
        "Seed Alpha4 subject identity mismatch",
    )
    require(
        "PAIR ASET-COMPONENT-OBSERVE-UNKNOWN OBSERVE-UNKNOWN ObserveUnknown "
        "ObserveUnknownPairing" in seed,
        "Seed Alpha4 OBSERVE-UNKNOWN pair unavailable",
    )


def validate_network_surface() -> None:
    text = NETWORK.read_text(encoding="utf-8")
    for required in (
        "ASET-NETWORK 1 ASET-NETWORK-ALPHA4 alpha4",
        "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA",
        "STATE IMPORTS SET-OF-EXACT-IMPORT-OBSERVATIONS",
        "TRANSITION ADMIT-IMPORT",
        "SEED-PROJECTION ADMIT-IMPORT OBSERVE-UNKNOWN",
        "SEED-RECOGNITION-OWNER TARGET-LOCAL-SEED",
        "EFFECT-PERMITTED-BY-NETWORK NEVER",
    ):
        require(required in text, f"Network Alpha4 declaration missing: {required}")
    require("ALLOW" not in text and "BLOCK" not in text, "terminal recognition leaked into Network")
    forth = (ROOT / "network/alpha4/operational/components.forth").read_text(encoding="utf-8")
    require(forth.count(";") == 3, "Network Alpha4 operational expression must have 3 words")
    require("LOCAL-ALLOW!" not in forth and "LOCAL-BLOCK!" not in forth, "Seed authority leaked")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path)
    args = parser.parse_args()
    validate_network_surface()
    sources = parse_binding()
    if args.seed_root is not None:
        validate_seed_root(args.seed_root.resolve(), sources)
        print("ALPHA4_NETWORK_SEED_CONTENT_BINDING=PASS")
    else:
        print("ALPHA4_NETWORK_SEED_CONTENT_BINDING=DECLARED")
    print("ALPHA4_NETWORK_SINGLE_STATE=IMPORTS")
    print("ALPHA4_NETWORK_SINGLE_TRANSITION=ADMIT-IMPORT")
    print("ALPHA4_NETWORK_TERMINAL_RECOGNITION_STATE=ABSENT")
    print("ALPHA4_NETWORK_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
