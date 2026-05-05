from __future__ import annotations

import json

import pandas as pd
import pytest

from src.views import build_events_json, build_main_page_json


@pytest.fixture
def stub_external(monkeypatch: pytest.MonkeyPatch) -> None:
    def _rates(
        currencies: list[str],
        fallback: dict | None = None,
        timeout: float = 10.0,
    ):
        return [{"currency": c, "rate": 10.0} for c in currencies]

    def _stocks(
        tickers: list[str],
        fallback: dict | None = None,
        timeout: float = 10.0,
    ):
        return [{"stock": t, "price": 100.0} for t in tickers]

    monkeypatch.setattr("src.views.fetch_currency_rates_rub", _rates)
    monkeypatch.setattr("src.views.fetch_stock_prices", _stocks)


def test_main_page_greeting_cards_top5_formats(
    sample_operations_df: pd.DataFrame, stub_external: None
) -> None:
    raw = build_main_page_json("2020-05-20 14:30:00", sample_operations_df)
    data = json.loads(raw)
    assert data["greeting"] == "Добрый день"
    assert len(data["cards"]) >= 1
    for c in data["cards"]:
        assert "last_digits" in c and "total_spent" in c and "cashback" in c
    assert len(data["top_transactions"]) == 5
    amounts = [t["amount"] for t in data["top_transactions"]]
    assert amounts == sorted(amounts, reverse=True)
    for t in data["top_transactions"]:
        assert len(t["date"].split(".")) == 3
        assert set(t.keys()) >= {"date", "amount", "category", "description"}
    for r in data["currency_rates"]:
        assert "currency" in r and "rate" in r and r["rate"] > 0
    for s in data["stock_prices"]:
        assert isinstance(s["stock"], str) and s["price"] > 0


def test_events_top7_and_transfers_cash(
    sample_operations_df: pd.DataFrame, stub_external: None
) -> None:
    raw = build_events_json("2020-05-20", sample_operations_df, "M")
    data = json.loads(raw)
    main = data["expenses"]["main"]
    if any(x["category"] == "Остальное" for x in main):
        assert len([x for x in main if x["category"] != "Остальное"]) == 7
    tnc = data["expenses"]["transfers_and_cash"]
    labels = {x["category"] for x in tnc}
    assert labels <= {"Наличные", "Переводы"}
    assert data["expenses"]["total"] >= 0
    assert data["income"]["total"] >= 0
