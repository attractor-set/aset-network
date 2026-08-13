from __future__ import annotations

from tools.alpha4_network_causal_expression import load_causal_nets
from tools.alpha4_network_triangulated_expression import check_triangulated_assurance


def test_every_active_network_subject_has_causal_representation() -> None:
    nets = load_causal_nets()
    assert set(nets) == {
        "network",
        "dynamic",
        "federation",
        "liveness",
        "federation-liveness",
    }
    assert {key: len(net.transitions) for key, net in nets.items()} == {
        "network": 3,
        "dynamic": 2,
        "federation": 6,
        "liveness": 4,
        "federation-liveness": 6,
    }
    assert all(net.semantic_precedence == "NONE" for net in nets.values())


def test_network_core_and_all_profiles_are_bounded_three_way_congruent() -> None:
    evidence = check_triangulated_assurance()
    assert evidence["representations"] == ("OPERATIONAL", "RELATIONAL", "CAUSAL")
    assert evidence["semantic_precedence"] == "NONE"
    assert evidence["semantic_delta"] == "NONE"
    assert evidence["pairwise_relations"] == {
        "operational_relational": "PASS",
        "operational_causal": "PASS",
        "relational_causal": "PASS",
    }
    assert evidence["core_cases"] == 272
    assert evidence["dynamic_cases"] == 10
    assert evidence["federation_states"] == 20
    assert evidence["federation_edges"] == 25
    assert evidence["liveness_cases"] == 51
    assert evidence["composition_cases"] == 88
    assert evidence["total_cases"] == 446
    assert evidence["status"] == "PASS"


def test_causal_sources_do_not_replace_relational_temporal_assurance() -> None:
    nets = load_causal_nets()
    assert nets["liveness"].mode == "PREDICATE"
    assert nets["federation-liveness"].mode == "PREDICATE"
