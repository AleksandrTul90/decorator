"""Загрузка курсов валют и котировок акций через requests с обработкой ошибок."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Бесплатные источники без ключа; при сбое используются значения из user_settings
EXCHANGE_HOST = "https://api.exchangerate.host"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"


def _rub_per_unit_foreign(rates_from_api: dict[str, float], code: str) -> float:
    """Ответ base=RUB: rates[USD] — USD за 1 RUB; возвращаем RUB за 1 USD."""
    code = code.upper()
    if code == "RUB":
        return 1.0
    per_rub = float(rates_from_api.get(code, 0.0) or 0.0)
    if per_rub <= 0:
        return 0.0
    return 1.0 / per_rub


def fetch_currency_rates_rub(
    currencies: list[str],
    fallback: dict[str, float] | None = None,
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    """Список {currency, rate}: сколько RUB за 1 единицу валюты (> 0)."""
    fallback = fallback or {}
    codes = [c.strip().upper() for c in currencies if isinstance(c, str) and c.strip()]
    codes = [c for c in codes if c != "RUB"]
    result: list[dict[str, Any]] = []

    rates_map: dict[str, float] = {}
    try:
        sym = ",".join(codes) if codes else "USD"
        url = f"{EXCHANGE_HOST}/latest"
        resp = requests.get(
            url,
            params={"base": "RUB", "symbols": sym},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", True) and "rates" not in data:
            raise ValueError(f"exchangerate.host: {data}")
        rates_map = {k.upper(): float(v) for k, v in data.get("rates", {}).items()}
        logger.info("Курсы валют получены с exchangerate.host")
    except Exception:
        logger.exception("Не удалось получить курсы валют из API, используем fallback")
        rates_map = {}

    for code in codes:
        rate = _rub_per_unit_foreign(rates_map, code) if rates_map else 0.0
        if rate <= 0:
            rate = float(fallback.get(code, 0.0) or 0.0)
        if rate <= 0:
            rate = 1.0
            logger.warning("Для %s нет курса, подставлен 1.0", code)
        result.append({"currency": code, "rate": float(rate)})
    return result


def _yahoo_symbol(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.endswith(".ME") or "." in t:
        return t
    return f"{t}"


def fetch_stock_prices(
    tickers: list[str],
    fallback: dict[str, float] | None = None,
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    """Список {stock, price}, price > 0."""
    fallback = fallback or {}
    out: list[dict[str, Any]] = []
    for raw in tickers:
        if not isinstance(raw, str) or not raw.strip():
            continue
        symbol = raw.strip().upper()
        price = 0.0
        try:
            sym = _yahoo_symbol(symbol)
            url = f"{YAHOO_CHART}/{sym}"
            r = requests.get(
                url,
                params={"interval": "1d", "range": "1d"},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (coursework)"},
            )
            r.raise_for_status()
            js = r.json()
            chart = js.get("chart", {})
            res = chart.get("result") or []
            if not res:
                raise ValueError("empty chart result")
            meta = res[0].get("meta") or {}
            price = float(
                meta.get("regularMarketPrice") or meta.get("previousClose") or 0.0
            )
            logger.info("Котировка %s: %s", symbol, price)
        except Exception:
            logger.exception("Ошибка Yahoo для %s", symbol)
            price = float(fallback.get(symbol, 0.0) or 0.0)
        if price <= 0:
            price = float(fallback.get(symbol, 1.0) or 1.0)
            logger.warning("Для акции %s подставлена цена fallback %s", symbol, price)
        out.append({"stock": symbol, "price": float(price)})
    return out
