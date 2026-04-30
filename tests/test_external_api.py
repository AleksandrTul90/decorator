from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.external_api import convert_to_rub, transaction_amount_rub


def test_transaction_amount_rub_rub_does_not_call_http() -> None:
    tx = {
        "operationAmount": {
            "amount": "10.5",
            "currency": {"code": "RUB", "name": "руб."},
        }
    }
    with patch("src.external_api.requests.get") as get:
        assert transaction_amount_rub(tx) == pytest.approx(10.5)
        get.assert_not_called()


def test_transaction_amount_rub_usd_converts_via_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APILAYER_API_KEY", "test-key")
    tx = {
        "operationAmount": {
            "amount": "2",
            "currency": {"code": "USD", "name": "USD"},
        }
    }

    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"result": 200.0}

    with patch("src.external_api.requests.get", return_value=resp) as get:
        assert transaction_amount_rub(tx) == pytest.approx(200.0)
        get.assert_called_once()


def test_convert_to_rub_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APILAYER_API_KEY", "test-key")
    resp = Mock()
    resp.status_code = 500
    resp.json.return_value = {"message": "oops"}

    with patch("src.external_api.requests.get", return_value=resp):
        with pytest.raises(RuntimeError):
            convert_to_rub(1.0, "USD")

