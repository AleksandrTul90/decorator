"""Общие утилиты: даты, приветствие, нормализация транзакций, настройки."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Маппинг типичных заголовков выгрузки Т-Банка → внутренние имена колонок
COLUMN_ALIASES: dict[str, str] = {
    "дата операции": "operation_date",
    "дата платежа": "payment_date",
    "номер карты": "card_last4",
    "статус": "status",
    "сумма операции": "amount_operation",
    "валюта операции": "currency_operation",
    "сумма платежа": "amount_payment",
    "валюта платежа": "currency_payment",
    "кешбэк": "cashback",
    "кэшбэк": "cashback",
    "кэшбек": "cashback",
    "категория": "category",
    "mcc": "mcc",
    "описание": "description",
    "бонусы (включая кешбэк)": "bonuses",
    "округление на «инвесткопилку»": "invest_rounding",
    "округление на \"инвесткопилку\"": "invest_rounding",
    "сумма операции с округлением": "amount_operation_rounded",
}


def greeting_for_datetime(dt: datetime) -> str:
    """Приветствие по локальному времени суток (критерии курсовой)."""
    h = dt.hour
    if 6 <= h <= 11:
        return "Доброе утро"
    if 12 <= h <= 17:
        return "Добрый день"
    if 18 <= h <= 22:
        return "Добрый вечер"
    return "Доброй ночи"


def parse_main_page_datetime(value: str) -> datetime:
    """Строка формата YYYY-MM-DD HH:MM:SS."""
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")


def parse_date_only(value: str) -> date:
    """Дата YYYY-MM-DD или dd.mm.yyyy."""
    s = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Неподдерживаемый формат даты: {value!r}")


def _normalize_col_name(name: Any) -> str:
    if not isinstance(name, str):
        return ""
    return " ".join(name.strip().lower().split())


def normalize_transactions_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит DataFrame выгрузки к единым английским колонкам."""
    rename: dict[str, str] = {}
    for c in df.columns:
        key = _normalize_col_name(str(c))
        if key in COLUMN_ALIASES:
            rename[str(c)] = COLUMN_ALIASES[key]
    out = df.rename(columns=rename)
    # Fallback: иногда заголовки выгрузки оказываются в неправильной кодировке.
    # Если ничего не переименовали, предполагаем стандартный порядок колонок.
    if not rename and len(out.columns) >= 11:
        ordered = list(out.columns)
        # Ожидаемый порядок из задания (15 колонок).
        expected = [
            "operation_date",
            "payment_date",
            "card_last4",
            "status",
            "amount_operation",
            "currency_operation",
            "amount_payment",
            "currency_payment",
            "cashback",
            "category",
            "mcc",
            "description",
            "bonuses",
            "invest_rounding",
            "amount_operation_rounded",
        ]
        if len(ordered) >= len(expected):
            out = out.rename(columns=dict(zip(ordered[: len(expected)], expected)))
    needed = [
        "operation_date",
        "payment_date",
        "card_last4",
        "status",
        "amount_operation",
        "currency_operation",
        "amount_payment",
        "currency_payment",
        "cashback",
        "category",
        "description",
    ]
    for col in needed:
        if col not in out.columns:
            out[col] = None
    out["operation_date"] = pd.to_datetime(
        out["operation_date"], errors="coerce", dayfirst=True
    )
    out["payment_date"] = pd.to_datetime(
        out["payment_date"], errors="coerce", dayfirst=True
    )
    for col in ("amount_operation", "amount_payment", "cashback"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["status"] = out["status"].astype(str)
    out["category"] = out["category"].fillna("").astype(str)
    out["description"] = out["description"].fillna("").astype(str)
    out["card_last4"] = out["card_last4"].apply(_normalize_card_last4)
    return out


def _normalize_card_last4(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) >= 4:
        return digits[-4:]
    return digits or None


def load_user_settings(path: str | Path | None = None) -> dict[str, Any]:
    """Читает user_settings.json (валюты, акции, запасные курсы)."""
    base = (
        Path(path)
        if path
        else Path(__file__).resolve().parent.parent / "user_settings.json"
    )
    with open(base, "r", encoding="utf-8") as f:
        return json.load(f)


def read_tinkoff_operations_excel(path: str | Path) -> pd.DataFrame:
    """Считывает Excel (.xls/.xlsx) с операциями и нормализует колонки."""
    p = Path(path)
    logger.info("Чтение операций из %s", p)
    try:
        df = pd.read_excel(p)
    except Exception:
        logger.exception("Ошибка pandas.read_excel для %s", p)
        raise
    return normalize_transactions_dataframe(df)


def filter_successful(df: pd.DataFrame) -> pd.DataFrame:
    """Только успешные операции (OK)."""
    if df.empty:
        return df
    st = df["status"].astype(str).str.upper()
    return df.loc[st.isin({"OK", "EXECUTED"})].copy()


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date


def events_date_range(anchor: date, mode: str = "M") -> DateRange:
    """Диапазон «События»: W / M / Y / ALL (ALL — от 1900-01-01; уточните в views)."""
    mode_u = (mode or "M").strip().upper()
    if mode_u == "W":
        start = anchor - timedelta(days=anchor.weekday())
        return DateRange(start=start, end=anchor)
    if mode_u == "M":
        start = anchor.replace(day=1)
        return DateRange(start=start, end=anchor)
    if mode_u == "Y":
        start = date(anchor.year, 1, 1)
        return DateRange(start=start, end=anchor)
    if mode_u == "ALL":
        return DateRange(start=date(1900, 1, 1), end=anchor)
    raise ValueError(f"Неизвестный режим диапазона: {mode!r}")


def slice_by_operation_date(df: pd.DataFrame, dr: DateRange) -> pd.DataFrame:
    """Фильтр по дате операции [start, end]."""
    if df.empty:
        return df
    d = df["operation_date"].dt.date
    return df.loc[(d >= dr.start) & (d <= dr.end)].copy()


def main_page_date_range(anchor: datetime) -> DateRange:
    """С начала месяца якорной даты по саму дату (день якоря)."""
    d = anchor.date()
    start = d.replace(day=1)
    return DateRange(start=start, end=d)
