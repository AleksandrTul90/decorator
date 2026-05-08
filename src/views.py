"""JSON-представления для веб-страниц «Главная» и «События»."""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd

from src.external_data import fetch_currency_rates_rub, fetch_stock_prices
from src.utils import (
    DateRange,
    events_date_range,
    filter_successful,
    greeting_for_datetime,
    load_user_settings,
    main_page_date_range,
    parse_main_page_datetime,
    parse_date_only,
    slice_by_operation_date,
)

logger = logging.getLogger(__name__)


def _aggregate_expenses_income(
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    """Расходы (платёж < 0) и поступления (> 0) по категориям, суммы по модулю."""
    if df.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    exp = df.loc[pay < 0].copy()
    inc = df.loc[pay > 0].copy()
    exp_pay = pd.to_numeric(exp["amount_payment"], errors="coerce")
    exp_sum = (
        exp.assign(_a=-exp_pay).groupby(exp["category"].fillna(""))["_a"].sum()
    )
    inc_sum = inc.groupby(inc["category"].fillna(""))["amount_payment"].sum()
    return exp_sum, inc_sum


def _top7_and_other(s: pd.Series) -> list[dict[str, Any]]:
    """Топ-7 категорий по убыванию + «Остальное», суммы округлены до целых."""
    s = s.sort_values(ascending=False)
    if s.empty:
        return []
    if len(s) <= 7:
        return [
            {"category": str(idx), "amount": int(round(float(val)))}
            for idx, val in s.items()
        ]
    top = s.head(7)
    rest = float(s.iloc[7:].sum())
    items = [
        {"category": str(idx), "amount": int(round(float(val)))}
        for idx, val in top.items()
    ]
    items.append({"category": "Остальное", "amount": int(round(rest))})
    return items


def _transfers_and_cash_section(exp_by_cat: pd.Series) -> list[dict[str, Any]]:
    """Категории «Наличные» и «Переводы», по убыванию суммы."""
    keys = ["Наличные", "Переводы"]
    parts: list[tuple[str, float]] = []
    for k in keys:
        if k in exp_by_cat.index:
            parts.append((k, float(exp_by_cat.loc[k])))
    parts.sort(key=lambda x: x[1], reverse=True)
    return [{"category": c, "amount": int(round(a))} for c, a in parts]


def build_main_page_json(
    date_time_str: str,
    transactions_df: pd.DataFrame,
    settings: dict[str, Any] | None = None,
) -> str:
    """
    JSON для «Главная»: приветствие по времени, карты, топ-5 транзакций, курсы, акции.
    """
    settings = settings or load_user_settings()
    dt = parse_main_page_datetime(date_time_str)
    dr = main_page_date_range(dt)
    df = filter_successful(transactions_df)
    df = slice_by_operation_date(df, dr)
    greeting = greeting_for_datetime(dt)

    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    cards_raw = df.loc[pay < 0].copy()
    cards_raw["spent"] = -pay.loc[pay < 0]

    card_rows: list[dict[str, Any]] = []
    if not cards_raw.empty and cards_raw["card_last4"].notna().any():
        for last4, g in cards_raw.groupby("card_last4"):
            if last4 is None or str(last4) == "nan":
                continue
            total = float(g["spent"].sum())
            total_spent = round(total, 2)
            card_rows.append(
                {
                    "last_digits": str(last4),
                    "total_spent": total_spent,
                    # 1 рубль кешбэка на каждые 100 рублей трат
                    "cashback": round(total_spent / 100.0, 2),
                }
            )
    card_rows.sort(key=lambda x: x["last_digits"])

    # Топ-5 по сумме платежа (знак сохраняем).
    pay_amount = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    top_df = df.loc[pay_amount.sort_values(ascending=False).head(5).index]
    top_transactions: list[dict[str, Any]] = []
    for _, row in top_df.iterrows():
        op_d = row.get("operation_date") if hasattr(row, "get") else row["operation_date"]
        pay_d = row.get("payment_date") if hasattr(row, "get") and "payment_date" in row else None

        chosen = None
        if op_d is not None and not pd.isna(op_d):
            chosen = op_d
        elif pay_d is not None and not pd.isna(pay_d):
            chosen = pay_d

        if hasattr(chosen, "strftime"):
            d_str = chosen.strftime("%d.%m.%Y")
        elif isinstance(chosen, str) and chosen.strip():
            d_str = parse_date_only(chosen).strftime("%d.%m.%Y")
        else:
            d_str = ""

        amt = float(pd.to_numeric(row["amount_payment"], errors="coerce") or 0.0)
        top_transactions.append(
            {
                "date": d_str,
                "amount": round(amt, 2),
                "category": str(row.get("category", "") or ""),
                "description": str(row.get("description", "") or ""),
            }
        )

    fb_rates = settings.get("fallback_currency_rates") or {}
    fb_stocks = settings.get("fallback_stock_prices") or {}
    currencies = list(settings.get("user_currencies") or [])
    stocks = list(settings.get("user_stocks") or [])

    currency_rates = fetch_currency_rates_rub(currencies, fallback=fb_rates)
    stock_prices = fetch_stock_prices(stocks, fallback=fb_stocks)

    payload = {
        "greeting": greeting,
        "cards": card_rows,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_events_json(
    date_str: str,
    transactions_df: pd.DataFrame,
    range_mode: str = "M",
    settings: dict[str, Any] | None = None,
) -> str:
    """JSON «События»: расходы/поступления, топ-7, переводы/наличные, рынки."""
    settings = settings or load_user_settings()
    anchor = parse_date_only(date_str)
    df_all = filter_successful(transactions_df)
    if range_mode.upper().strip() == "ALL" and not df_all.empty:
        min_d = df_all["operation_date"].min()
        start = min_d.date() if pd.notna(min_d) and hasattr(min_d, "date") else anchor
        dr = DateRange(start=start, end=anchor)
    else:
        dr = events_date_range(anchor, range_mode)
    df = slice_by_operation_date(df_all, dr)

    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    total_expenses = float((-pay[pay < 0]).sum())
    total_income = float(pay[pay > 0].sum())

    exp_by_cat, inc_by_cat = _aggregate_expenses_income(df)

    expenses_block = {
        "total": int(round(total_expenses)),
        "main": _top7_and_other(exp_by_cat),
        "transfers_and_cash": _transfers_and_cash_section(exp_by_cat),
    }
    income_block = {
        "total": int(round(total_income)),
        "main": _top7_and_other(inc_by_cat),
    }

    fb_rates = settings.get("fallback_currency_rates") or {}
    fb_stocks = settings.get("fallback_stock_prices") or {}
    currencies = list(settings.get("user_currencies") or [])
    stocks = list(settings.get("user_stocks") or [])

    currency_rates = fetch_currency_rates_rub(currencies, fallback=fb_rates)
    stock_prices = fetch_stock_prices(stocks, fallback=fb_stocks)

    payload = {
        "expenses": expenses_block,
        "income": income_block,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main_page_view(date_time_str: str, transactions_df: pd.DataFrame) -> dict[str, Any]:
    """Словарь (не строка) для тестов и программного использования."""
    return json.loads(build_main_page_json(date_time_str, transactions_df))


def events_view(
    date_str: str, transactions_df: pd.DataFrame, range_mode: str = "M"
) -> dict[str, Any]:
    return json.loads(build_events_json(date_str, transactions_df, range_mode))
