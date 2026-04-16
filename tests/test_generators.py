"""Тесты модуля generators."""

import pytest

from src.generators import (
    card_number_generator,
    filter_by_currency,
    transaction_descriptions,
)


@pytest.mark.parametrize(
    "currency,expected_ids",
    [
        ("USD", [939719570, 142264268, 895315941]),
        ("RUB", [873106923, 594226727]),
        ("EUR", []),
    ],
)
def test_filter_by_currency_matches_code(sample_transactions, currency, expected_ids):
    result = list(filter_by_currency(sample_transactions, currency))
    assert [t["id"] for t in result] == expected_ids


def test_filter_by_currency_empty_list():
    assert list(filter_by_currency([], "USD")) == []


def test_filter_by_currency_no_matches_not_error(sample_transactions):
    gen = filter_by_currency(sample_transactions, "GBP")
    assert list(gen) == []


def test_filter_by_currency_skips_malformed(transactions_with_broken_entry):
    usd = list(filter_by_currency(transactions_with_broken_entry, "USD"))
    assert [t["id"] for t in usd] == [939719570, 142264268]


@pytest.mark.parametrize(
    "take,expected_prefixes",
    [
        (2, ["Перевод организации", "Перевод со счета на счет"]),
        (
            5,
            [
                "Перевод организации",
                "Перевод со счета на счет",
                "Перевод со счета на счет",
                "Перевод с карты на карту",
                "Перевод организации",
            ],
        ),
    ],
)
def test_transaction_descriptions_sequence(sample_transactions, take, expected_prefixes):
    gen = transaction_descriptions(sample_transactions)
    out = [next(gen) for _ in range(take)]
    assert out == expected_prefixes


def test_transaction_descriptions_empty():
    assert list(transaction_descriptions([])) == []


@pytest.mark.parametrize(
    "extra,count",
    [
        ([], 0),
        ([{"description": "One"}], 1),
        (
            [
                {"description": "A"},
                {"description": "B"},
                {"no_description": True},
            ],
            3,
        ),
    ],
)
def test_transaction_descriptions_varying_lengths(extra, count):
    rows = list(extra)
    gen = transaction_descriptions(rows)
    result = list(gen)
    assert len(result) == count
    if count >= 3:
        assert result[2] == ""


@pytest.mark.parametrize(
    "start,stop,expected",
    [
        (1, 5, [f"0000 0000 0000 000{i}" for i in range(1, 6)]),
        (1, 1, ["0000 0000 0000 0001"]),
        (
            10,
            12,
            [
                "0000 0000 0000 0010",
                "0000 0000 0000 0011",
                "0000 0000 0000 0012",
            ],
        ),
    ],
)
def test_card_number_generator_range_and_format(start, stop, expected):
    assert list(card_number_generator(start, stop)) == expected


def test_card_number_generator_invalid_range_is_empty():
    assert list(card_number_generator(5, 1)) == []


def test_card_number_generator_empty_after_clamp():
    assert list(card_number_generator(-5, 0)) == []


@pytest.mark.parametrize(
    "start,stop",
    [
        (9999_9999_9999_9999, 9999_9999_9999_9999),
        (9999_9999_9999_9998, 9999_9999_9999_9999),
    ],
)
def test_card_number_generator_high_end(start, stop):
    cards = list(card_number_generator(start, stop))
    assert len(cards) == stop - start + 1
    assert all(len(c) == 19 and c.count(" ") == 3 for c in cards)
    assert cards[-1] == "9999 9999 9999 9999"


def test_card_number_generator_clamps_stop_above_max():
    out = list(
        card_number_generator(9_999_9999_9999_9998, 9_999_9999_9999_9999_9999)
    )
    assert out == [
        "9999 9999 9999 9998",
        "9999 9999 9999 9999",
    ]


def test_card_number_generator_clamps_start_below_one():
    assert list(card_number_generator(0, 2)) == [
        "0000 0000 0000 0001",
        "0000 0000 0000 0002",
    ]

