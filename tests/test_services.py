from __future__ import annotations

import json

import pandas as pd
import pytest

from src.services import (
    investment_bank,
    profitable_cashback_categories_json,
    simple_search_json,
    transactions_with_phone_json,
    transfers_to_individuals_json,
)


def test_profitable_cashback_json_valid_and_top_categories(
    sample_operations_df: pd.DataFrame,
) -> None:
    raw = profitable_cashback_categories_json(sample_operations_df, 2020, 5)
    data = json.loads(raw)
    assert len(data) >= 3
    assert sum(data.values()) > 0


def test_investment_bank_rounding() -> None:
    txs = [
        {"Дата операции": "2020-05-10", "Сумма операции": -1712.0},
        {"Дата операции": "2020-05-11", "Сумма операции": 100.0},
    ]
    assert investment_bank("2020-05", txs, 50) == pytest.approx(38.0)


def test_simple_search_substring_case_insensitive() -> None:
    rows = [
        {"description": "Покупка КНИГИ", "category": "Разное"},
        {"description": "продукты", "category": "Еда"},
        {"description": "другое", "category": "Книги"},
    ]
    raw = simple_search_json(rows, "книг")
    found = json.loads(raw)
    assert len(found) == 2


def test_phone_search_variants() -> None:
    rows = [
        {"description": "МТС +7 (921) 111-22-33"},
        {"description": "Я МТС +7 921 11-22-33"},
        {"description": "без номера"},
        {"description": "Тинькофф Мобайл 89000000000"},
    ]
    raw = transactions_with_phone_json(rows)
    found = json.loads(raw)
    assert len(found) == 3


def test_transfers_to_individuals() -> None:
    rows = [
        {"category": "Переводы", "description": "Александр Жматович"},
        {"category": "Переводы", "description": "Сервис переводов"},
        {"category": "Переводы", "description": "Иван П."},
        {"category": "Другое", "description": "Александр Жматович"},
    ]
    raw = transfers_to_individuals_json(rows)
    found = json.loads(raw)
    assert len(found) == 2


def test_transfers_to_individuals_name_not_only_at_line_start() -> None:
    """Имя и инициал могут идти после текста банка (критерий методички)."""
    rows = [
        {
            "category": "Переводы",
            "description": "Перевод между счетами. Получатель Валерий А.",
        },
        {"category": "Переводы", "description": "Сервис переводов"},
    ]
    raw = transfers_to_individuals_json(rows)
    found = json.loads(raw)
    assert len(found) == 1


def test_phone_format_parentheses_and_leading_8() -> None:
    rows = [
        {"description": "Оплата +7 (900) 000-00-00 подписка"},
        {"description": "Связь 89000000000"},
        {"description": "без телефона"},
    ]
    raw = transactions_with_phone_json(rows)
    found = json.loads(raw)
    assert len(found) == 2
