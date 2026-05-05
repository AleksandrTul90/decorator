"""Отчёты по транзакциям и декоратор записи результата в файл."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

import pandas as pd

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def report_to_file(
    arg: str | Path | Callable[..., Any] | None = None,
) -> Callable[[F], F] | F:
    """
    - @report_to_file → файл ``<имя_функции>_report.json``;
    - @report_to_file("custom.json") → заданное имя.
    """

    def decorate(func: F, explicit_path: str | Path | None) -> F:
        default_path = Path(f"{func.__name__}_report.json")
        out_path = Path(explicit_path) if explicit_path is not None else default_path

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            logger.info("Сохранение отчёта %s → %s", func.__name__, out_path)
            _write_report_result(out_path, result)
            return result

        return cast(F, wrapper)

    if callable(arg):
        return decorate(arg, None)
    return lambda func: decorate(func, arg)


def _write_report_result(path: Path, result: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(result, pd.DataFrame):
        path.write_text(
            result.to_json(orient="records", force_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)


def _parse_report_date(value: str | None) -> date:
    if not value:
        return datetime.now().date()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Неверная дата отчёта: {value!r}")


def _three_month_window(end: date) -> tuple[date, date]:
    """Окно ~90 дней до конечной даты (включительно)."""
    start = end - timedelta(days=90)
    return start, end


@report_to_file
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    report_date: str | None = None,
) -> pd.DataFrame:
    """Траты по категории за последние три месяца от даты отчёта."""
    end = _parse_report_date(report_date)
    start, _ = _three_month_window(end)
    if transactions.empty:
        return pd.DataFrame()
    df = transactions.copy()
    df["operation_date"] = pd.to_datetime(df["operation_date"], errors="coerce")
    d = df["operation_date"].dt.date
    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    mask = (
        (d >= start)
        & (d <= end)
        & (df["category"].fillna("") == category)
        & (pay < 0)
    )
    return df.loc[
        mask, ["operation_date", "category", "amount_payment", "description"]
    ].copy()


@report_to_file
def spending_by_weekday(
    transactions: pd.DataFrame,
    report_date: str | None = None,
) -> pd.DataFrame:
    """Средние траты по дням недели за последние три месяца."""
    end = _parse_report_date(report_date)
    start, _ = _three_month_window(end)
    if transactions.empty:
        return pd.DataFrame(columns=["weekday", "average_spending"])
    df = transactions.copy()
    df["operation_date"] = pd.to_datetime(df["operation_date"], errors="coerce")
    d = df["operation_date"].dt.date
    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    sub = df.loc[(d >= start) & (d <= end) & (pay < 0)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["weekday", "average_spending"])
    sub["spent"] = -pd.to_numeric(sub["amount_payment"], errors="coerce")
    sub["weekday"] = pd.to_datetime(sub["operation_date"]).dt.day_name()
    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    g = sub.groupby("weekday")["spent"].mean().reindex(order).dropna()
    out = g.reset_index().rename(columns={"spent": "average_spending"})
    out["average_spending"] = out["average_spending"].round(2)
    return out


@report_to_file
def spending_by_workday(
    transactions: pd.DataFrame,
    report_date: str | None = None,
) -> pd.DataFrame:
    """Средние траты в рабочий и выходной день за последние три месяца."""
    end = _parse_report_date(report_date)
    start, _ = _three_month_window(end)
    if transactions.empty:
        return pd.DataFrame(columns=["day_type", "average_spending"])
    df = transactions.copy()
    df["operation_date"] = pd.to_datetime(df["operation_date"], errors="coerce")
    d = df["operation_date"].dt.date
    pay = pd.to_numeric(df["amount_payment"], errors="coerce").fillna(0.0)
    sub = df.loc[(d >= start) & (d <= end) & (pay < 0)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["day_type", "average_spending"])
    sub["spent"] = -pd.to_numeric(sub["amount_payment"], errors="coerce")
    wd = pd.to_datetime(sub["operation_date"]).dt.weekday
    sub["day_type"] = wd.apply(lambda x: "weekday" if x < 5 else "weekend")
    g = sub.groupby("day_type")["spent"].mean().reset_index()
    g = g.rename(columns={"spent": "average_spending"})
    g["average_spending"] = g["average_spending"].round(2)
    order_map = {"weekday": 0, "weekend": 1}
    g["_o"] = g["day_type"].map(order_map)
    return g.sort_values("_o").drop(columns="_o").reset_index(drop=True)
