from __future__ import annotations

from pathlib import Path

import pytest

from tools.alpha4_network_causal_expression import (
    CausalExpressionError,
    load_causal_nets,
    parse_causal_net,
    validate_causal_contract,
)
from tools.alpha4_network_paired_expression import parse_operational_words
from tools.alpha4_network_profile_paired_expression import (
    EXPECTED_DYNAMIC_STACK_EFFECTS,
    EXPECTED_DYNAMIC_WORDS,
    require_words,
)
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
    assert evidence["operational_stack_contracts"] == 21
    assert evidence["causal_closed_world_contracts"] == 21
    assert evidence["federation_result_code_bindings"] == 6
    assert evidence["status"] == "PASS"


def test_causal_sources_do_not_replace_relational_temporal_assurance() -> None:
    nets = load_causal_nets()
    assert nets["liveness"].mode == "PREDICATE"
    assert nets["federation-liveness"].mode == "PREDICATE"


def _mutated_source(tmp_path: Path, source: Path, old: str, new: str) -> Path:
    target = tmp_path / source.name
    text = source.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return target


def test_core_operational_stack_contract_rejects_missing_observation(tmp_path: Path) -> None:
    source = Path("network/alpha4/operational/components.forth")
    mutated = _mutated_source(
        tmp_path,
        source,
        "( imports observation -- imports result )",
        "( imports -- imports result )",
    )
    with pytest.raises(RuntimeError, match="stack contract mismatch"):
        parse_operational_words(mutated)


def test_profile_operational_stack_contract_rejects_missing_seed_binding(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/dynamic/operational/components.forth")
    mutated = _mutated_source(
        tmp_path,
        source,
        "( binding seed-binding recognition -- flag )",
        "( binding recognition -- flag )",
    )
    with pytest.raises(RuntimeError, match="stack contract mismatch"):
        require_words(mutated, EXPECTED_DYNAMIC_WORDS, EXPECTED_DYNAMIC_STACK_EFFECTS)


def test_predicate_causal_output_is_closed_world(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/dynamic/causal/components.petri")
    mutated = _mutated_source(tmp_path, source, "OUTPUT VALUE TRUE", "OUTPUT VALUE FALSE")
    net = parse_causal_net(mutated, "ASET-NETWORK-DYNAMIC-ALPHA4-CAUSAL", "PREDICATE")
    with pytest.raises(CausalExpressionError, match="causal output contract drift"):
        validate_causal_contract("dynamic", net)


def test_causal_effect_surface_rejects_unbound_extra_effect(tmp_path: Path) -> None:
    source = Path("network/alpha4/causal/components.petri")
    mutated = _mutated_source(
        tmp_path,
        source,
        "EFFECT ADD_IMPORT",
        "EFFECT ADD_IMPORT\nEFFECT DESTROY_IMPORTS",
    )
    net = parse_causal_net(mutated, "ASET-NETWORK-ALPHA4-CAUSAL", "STATE-TRANSITION")
    with pytest.raises(CausalExpressionError, match="causal effect contract drift"):
        validate_causal_contract("network", net)


def test_federation_causal_result_code_is_closed_world(tmp_path: Path) -> None:
    source = Path("network/alpha4/profiles/federation/causal/components.petri")
    mutated = _mutated_source(
        tmp_path, source, "OUTPUT CODE FEDERATION_CREATED", "OUTPUT CODE WRONG_CODE"
    )
    net = parse_causal_net(mutated, "ASET-NETWORK-FEDERATION-ALPHA4-CAUSAL", "STATE-TRANSITION")
    with pytest.raises(CausalExpressionError, match="causal output contract drift"):
        validate_causal_contract("federation", net)
