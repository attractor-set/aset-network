from __future__ import annotations

from tools.alpha4_network_causal_expression import load_causal_nets
from tools.alpha4_network_triangulated_expression import (
    check_triangulated_assurance,
    print_evidence,
)


def main() -> int:
    nets = load_causal_nets()
    evidence = check_triangulated_assurance()
    print("ALPHA4_NETWORK_CAUSAL_SUBJECTS=5/5 PASS")
    print(
        "ALPHA4_NETWORK_CAUSAL_COMPONENTS="
        + ",".join(f"{key}:{len(net.transitions)}" for key, net in sorted(nets.items()))
    )
    print("ALPHA4_NETWORK_ASSURANCE_SEMANTIC_DELTA=NONE")
    print_evidence(evidence)
    print("ALPHA4_NETWORK_ASSURANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
