from __future__ import annotations

from tools.alpha4_network_profile_paired_expression import (
    COMPOSITION_FORTH,
    DYNAMIC_FORTH,
    EXPECTED_COMPOSITION_WORDS,
    EXPECTED_DYNAMIC_WORDS,
    EXPECTED_LIVENESS_WORDS,
    LIVENESS_FORTH,
    bounded_composition_pairing_check,
    bounded_dynamic_pairing_check,
    bounded_liveness_pairing_check,
    parse_operational_words,
)


def test_alpha4_dynamic_has_exact_operational_counterpart() -> None:
    assert parse_operational_words(DYNAMIC_FORTH) == EXPECTED_DYNAMIC_WORDS
    assert bounded_dynamic_pairing_check() == 10


def test_alpha4_liveness_has_exact_operational_counterpart() -> None:
    assert parse_operational_words(LIVENESS_FORTH) == EXPECTED_LIVENESS_WORDS
    assert bounded_liveness_pairing_check() == 51


def test_alpha4_federation_liveness_composition_has_exact_operational_counterpart() -> None:
    assert parse_operational_words(COMPOSITION_FORTH) == EXPECTED_COMPOSITION_WORDS
    assert bounded_composition_pairing_check() == 88


def test_alpha4_non_stateful_operational_pairing_is_bounded_without_adding_transitions() -> None:
    total = (
        bounded_dynamic_pairing_check()
        + bounded_liveness_pairing_check()
        + bounded_composition_pairing_check()
    )
    assert total == 149
