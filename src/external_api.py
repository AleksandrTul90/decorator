from __future__ import annotations

import os
from typing import Any, Mapping

import requests
from dotenv import load_dotenv

_API_BASE_URL = "https://api.apilayer.com/exchangerates_data"


def _get_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("APILAYER_API_KEY")
    if not api_key:
        raise RuntimeError("APILAYER_API_KEY is not set")
    return api_key


def convert_to_rub(amount: float, from_currency: str) -> float:
    """Convert ``amount`` from ``from_currency`` to RUB via Exchange Rates Data API."""
    if from_currency == "RUB":
        return float(amount)

    api_key = _get_api_key()
    resp = requests.get(
        f"{_API_BASE_URL}/convert",
        params={"from": from_currency, "to": "RUB", "amount": str(amount)},
        headers={"apikey": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Currency API error: HTTP {resp.status_code}")

    payload: Any = resp.json()
    if not isinstance(payload, dict) or "result" not in payload:
        raise RuntimeError("Currency API response has no 'result'")

    result = payload["result"]
    try:
        return float(result)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Currency API 'result' is not a number") from exc


def transaction_amount_rub(transaction: Mapping[str, Any]) -> float:
    """Return transaction amount in RUB as float.

    Expects the standard transaction shape used in this project:
    ``transaction['operationAmount']['amount']`` and
    ``transaction['operationAmount']['currency']['code']``.
    """
    op_amount = transaction.get("operationAmount")
    if not isinstance(op_amount, Mapping):
        return 0.0

    raw_amount = op_amount.get("amount")
    currency = op_amount.get("currency")
    if not isinstance(currency, Mapping):
        return 0.0

    currency_code = currency.get("code")
    if not isinstance(currency_code, str):
        return 0.0

    if not isinstance(raw_amount, (str, int, float)):
        return 0.0

    try:
        amount = float(raw_amount)
    except (TypeError, ValueError):
        return 0.0

    if currency_code in {"USD", "EUR"}:
        return convert_to_rub(amount, currency_code)
    return amount
