from __future__ import annotations

from src.operations_processing import process_bank_operations, process_bank_search


def test_process_bank_search_filters_by_description_case_insensitive() -> None:
    data = [
        {"description": "Перевод организации"},
        {"description": "Открытие вклада"},
        {"description": "перевод со счета на счет"},
        {"description": None},
        {},
    ]

    result = process_bank_search(data, "перевод")
    assert result == [
        {"description": "Перевод организации"},
        {"description": "перевод со счета на счет"},
    ]


def test_process_bank_search_empty_search_returns_empty_list() -> None:
    assert process_bank_search([{"description": "abc"}], "") == []


def test_process_bank_operations_counts_categories_by_description() -> None:
    data = [
        {"description": "Перевод организации"},
        {"description": "Открытие вклада"},
        {"description": "Перевод с карты на карту"},
        {"description": "Перевод со счета на счет"},
        {"description": None},
        {},
    ]

    result = process_bank_operations(
        data,
        categories=["перевод", "вклад"],
    )

    assert result["перевод"] == 3
    assert result["вклад"] == 1
