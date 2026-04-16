"""Функции-генераторы для фильтрации и форматирования финансовых данных."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

_MAX_CARD_NUMBER = 9999_9999_9999_9999


def filter_by_currency(
    transactions: list[dict[str, Any]],
    currency: str,
) -> Iterator[dict[str, Any]]:
    for transaction in transactions:
        try:
            op = transaction["operationAmount"]
            cur = op["currency"]
            code = cur["code"]
        except (KeyError, TypeError):
            continue
        if code == currency:
            yield transaction


def transaction_descriptions(
    transactions: list[dict[str, Any]],
) -> Iterator[str]:
    for transaction in transactions:
        yield str(transaction.get("description", ""))


def card_number_generator(start: int, stop: int) -> Iterator[str]:
    if start > stop:
        return
    lo = max(1, start)
    hi = min(_MAX_CARD_NUMBER, stop)
    if lo > hi:
        return
    for n in range(lo, hi + 1):
        digits = f"{n:016d}"
        yield f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"

