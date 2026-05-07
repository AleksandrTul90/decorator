from __future__ import annotations

import pytest

from src.external_data import fetch_currency_rates_rub, fetch_stock_prices


def test_currency_rates_positive_after_api_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*_a: object, **_k: object) -> None:
        raise ConnectionError("network down")

    monkeypatch.setattr("src.external_data.requests.get", _fail)
    out = fetch_currency_rates_rub(
        ["USD", "EUR"],
        fallback={"USD": 92.5, "EUR": 100.0},
    )
    assert len(out) == 2
    assert {x["currency"] for x in out} == {"USD", "EUR"}
    assert all(x["rate"] > 0 for x in out)


def test_stock_prices_positive_after_api_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*_a: object, **_k: object) -> None:
        raise ConnectionError("network down")

    monkeypatch.setattr("src.external_data.requests.get", _fail)
    out = fetch_stock_prices(
        ["AAPL", "TSLA"],
        fallback={"AAPL": 175.0, "TSLA": 250.0},
    )
    assert len(out) == 2
    assert all(isinstance(x["stock"], str) and x["price"] > 0 for x in out)
