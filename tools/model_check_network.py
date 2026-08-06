from __future__ import annotations

from itertools import product


def main() -> int:
    statuses = ("UNKNOWN", "ACCEPT", "DENY")
    enforcements = ("BLOCKED", "ALLOW")
    valid = {("UNKNOWN", "BLOCKED"), ("ACCEPT", "ALLOW"), ("DENY", "BLOCKED")}
    for status, enforcement in product(statuses, enforcements):
        derived_valid = (
            (status == "UNKNOWN" and enforcement == "BLOCKED")
            or (status == "ACCEPT" and enforcement == "ALLOW")
            or (status == "DENY" and enforcement == "BLOCKED")
        )
        assert derived_valid == ((status, enforcement) in valid)

    contexts = ("A", "B", "C")
    for source, target in product(contexts, repeat=2):
        route_valid = source != target
        assert route_valid == (source != target)

    print("OK: bounded decision and route model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
