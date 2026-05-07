"""Сервисы анализа операций (элементы функционального стиля: map, filter, reduce)."""

from __future__ import annotations

import json
import logging
import math
import re
from datetime import date, datetime
from functools import reduce
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Телефон: +7 (900) 000-00-00, +7 900 00-00-00, 89000000000 и т.п.
PHONE_PATTERN = re.compile(
    r"(?:\+7|8)(?:"
    r"\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}"
    r"|\s*\d{3}\s*\d{2}[-\s]?\d{2}[-\s]?\d{2}"
    r"|\s*\d{10}"
    r")|"
    r"\b8\d{10}\b",
    re.IGNORECASE,
)

# Перевод физлицу: «Имя Фамилия» или «Имя Ф.» в тексте описания (категория «Переводы»).
PERSON_TRANSFER_PATTERN = re.compile(
    r"(?:"
    r"[А-ЯЁA-ZЁ][а-яёa-zё]+\s+[А-ЯЁA-ZЁ][а-яёa-zё]+"
    r"|"
    r"[А-ЯЁA-ZЁ][а-яёa-zё]+\s+[А-ЯЁA-ZЁ]\."
    r")",
    re.UNICODE,
)


def _parse_op_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def profitable_cashback_categories_json(
    df_like: Any,
    year: int,
    month: int,
) -> str:
    """
    Сколько кешбэка по категориям за месяц (сумма поля «Кешбэк»).
    df_like — DataFrame после normalize или список словарей.
    """
    if hasattr(df_like, "to_dict"):
        rows = df_like.to_dict(orient="records")
    else:
        rows = list(df_like)

    def in_month(row: dict[str, Any]) -> bool:
        d = row.get("operation_date")
        if hasattr(d, "date"):
            dd = d.date() if hasattr(d, "date") else d
        elif isinstance(d, str):
            dd = _parse_op_date(d)
        else:
            dd = _parse_op_date(row.get("Дата операции"))
        if dd is None:
            return False
        return dd.year == year and dd.month == month

    def row_cash(row: dict[str, Any]) -> float:
        for key in ("cashback", "Кешбэк"):
            v = row.get(key)
            if v is not None:
                try:
                    val = float(v)
                    return 0.0 if math.isnan(val) else val
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def row_cat(row: dict[str, Any]) -> str:
        for key in ("category", "Категория"):
            v = row.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return "Без категории"

    filtered = list(filter(in_month, rows))
    pairs: Iterable[tuple[str, float]] = map(
        lambda r: (row_cat(r), row_cash(r)),
        filtered,
    )

    def reducer(
        acc: dict[str, float],
        item: tuple[str, float],
    ) -> dict[str, float]:
        k, v = item
        acc[k] = acc.get(k, 0.0) + v
        return acc

    totals = reduce(reducer, pairs, {})
    ranked = sorted(totals.items(), key=lambda x: -x[1])
    out = {k: int(round(v)) for k, v in ranked}
    return json.dumps(out, ensure_ascii=False, indent=2)


def investment_bank(
    month: str,
    transactions: list[dict[str, Any]],
    limit: int,
) -> float:
    """
    Сумма «Инвесткопилки»: округление трат вверх до кратного limit (10/50/100).
    """
    year_s, month_s = month.split("-")
    y, m = int(year_s), int(month_s)

    def amount_op(t: dict[str, Any]) -> float:
        for key in ("Сумма операции", "amount_operation"):
            if key in t and t[key] is not None:
                try:
                    return float(t[key])
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def is_expense(a: float) -> bool:
        return a < 0

    def round_up_contribution(a: float) -> float:
        x = abs(a)
        up = math.ceil(x / limit) * limit
        return float(up - x)

    def in_month(t: dict[str, Any]) -> bool:
        d = _parse_op_date(t.get("Дата операции") or t.get("operation_date"))
        return d is not None and d.year == y and d.month == m

    spent = filter(in_month, transactions)
    spent_neg = filter(lambda t: is_expense(amount_op(t)), spent)
    parts = map(round_up_contribution, map(amount_op, spent_neg))
    return float(sum(parts))


def simple_search_json(transactions: list[dict[str, Any]], query: str) -> str:
    """Подстрочный поиск без учёта регистра в описании и категории."""
    q = (query or "").lower()

    def matches(t: dict[str, Any]) -> bool:
        if not q:
            return False
        desc = str(t.get("description") or t.get("Описание") or "").lower()
        cat = str(t.get("category") or t.get("Категория") or "").lower()
        return q in desc or q in cat

    found = list(filter(matches, transactions))
    return json.dumps(found, ensure_ascii=False, indent=2, default=str)


def transactions_with_phone_json(transactions: list[dict[str, Any]]) -> str:
    """Транзакции, в описании которых есть мобильный номер."""

    def has_phone(t: dict[str, Any]) -> bool:
        desc = str(t.get("description") or t.get("Описание") or "")
        return bool(PHONE_PATTERN.search(desc))

    found = list(filter(has_phone, transactions))
    return json.dumps(found, ensure_ascii=False, indent=2, default=str)


def transfers_to_individuals_json(transactions: list[dict[str, Any]]) -> str:
    """Переводы физлицам: категория «Переводы» и шаблон имени в описании."""

    def is_transfer_person(t: dict[str, Any]) -> bool:
        cat = str(t.get("category") or t.get("Категория") or "").strip()
        if cat != "Переводы":
            return False
        desc = str(t.get("description") or t.get("Описание") or "").strip()
        return bool(PERSON_TRANSFER_PATTERN.search(desc))

    found = list(filter(is_transfer_person, transactions))
    return json.dumps(found, ensure_ascii=False, indent=2, default=str)
