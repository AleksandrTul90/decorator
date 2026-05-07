"""Точка входа курсовой: демонстрация веб-представлений, сервисов и отчётов."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    investment_bank,
    profitable_cashback_categories_json,
    simple_search_json,
    transactions_with_phone_json,
    transfers_to_individuals_json,
)
from src.utils import read_tinkoff_operations_excel
from src.views import build_events_json, build_main_page_json


def _default_data_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "operations.xlsx"


def _derive_demo_dates(df: pd.DataFrame) -> tuple[str, str, int, int]:
    """Строки даты/времени и год-месяц для демо по последней операции в выборке."""
    if df.empty:
        return "2020-05-20 14:30:00", "2020-05-20", 2020, 5
    ts = pd.to_datetime(df["operation_date"], errors="coerce").max()
    if pd.isna(ts):
        return "2020-05-20 14:30:00", "2020-05-20", 2020, 5
    d = ts.date() if hasattr(ts, "date") else ts
    dt_str = f"{d.year}-{d.month:02d}-{d.day:02d} 14:30:00"
    date_str = f"{d.year}-{d.month:02d}-{d.day:02d}"
    return dt_str, date_str, d.year, d.month


def _sample_expense_category(df: pd.DataFrame) -> str:
    """Категория для отчёта «траты по категории» — частая среди расходов."""
    if df.empty:
        return "Супермаркеты"
    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    cats = df.loc[pay < 0, "category"].dropna().astype(str)
    cats = cats[cats.str.len() > 0]
    if cats.empty:
        return "Супермаркеты"
    mode = cats.mode()
    return str(mode.iloc[0]) if not mode.empty else "Супермаркеты"


def _preview_json(text: str, max_len: int = 600) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... [фрагмент]"


def main(
    *,
    data_path: Path | None = None,
    load_operations: Callable[[Path], pd.DataFrame] | None = None,
) -> None:
    """
    Загружает операции из Excel, вызывает основные функции views / services / reports.

    Parameters
    ----------
    data_path
        Путь к .xlsx (по умолчанию ``data/operations.xlsx`` в корне проекта).
    load_operations
        Подмена загрузчика (для тестов).
    """
    loader = load_operations or read_tinkoff_operations_excel
    path = data_path if data_path is not None else _default_data_path()
    if load_operations is None and not path.is_file():
        raise SystemExit(f"Нет файла данных: {path}")

    df = loader(path)
    rows: list[dict[str, Any]] = df.to_dict(orient="records")
    dt_str, date_str, year, month = _derive_demo_dates(df)
    category = _sample_expense_category(df)

    print("=== Веб-страницы: JSON «Главная» (build_main_page_json) ===")
    print(_preview_json(build_main_page_json(dt_str, df)))

    print("\n=== Веб-страницы: JSON «События» (build_events_json) ===")
    print(_preview_json(build_events_json(date_str, df, range_mode="M")))

    print("\n=== Сервисы: кешбэк по категориям (profitable_cashback_categories_json) ===")
    print(profitable_cashback_categories_json(df, year, month))

    print("\n=== Сервисы: инвесткопилка за месяц (investment_bank) ===")
    ym = f"{year}-{month:02d}"
    print(f"month={ym}, limit=50 → сумма округлений: {investment_bank(ym, rows, 50)}")

    print("\n=== Сервисы: простой поиск (simple_search_json), запрос «перевод» ===")
    print(_preview_json(simple_search_json(rows, "перевод"), max_len=800))

    print("\n=== Сервисы: операции с телефоном в описании (transactions_with_phone_json) ===")
    print(_preview_json(transactions_with_phone_json(rows), max_len=800))

    print("\n=== Сервисы: переводы физлицам (transfers_to_individuals_json) ===")
    print(_preview_json(transfers_to_individuals_json(rows), max_len=800))

    print("\n=== Отчёты: траты по категории (spending_by_category) — файл *_report.json ===")
    print(spending_by_category(df, category, date_str))

    print("\n=== Отчёты: средние траты по дням недели (spending_by_weekday) ===")
    print(spending_by_weekday(df, date_str))

    print("\n=== Отчёты: рабочий vs выходной (spending_by_workday) ===")
    print(spending_by_workday(df, date_str))


if __name__ == "__main__":
    main()
