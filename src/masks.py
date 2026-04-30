from __future__ import annotations

import logging
import re
from pathlib import Path

_DIGITS_RE = re.compile(r"\d+")

_LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.FileHandler(_LOGS_DIR / "masks.log", mode="w", encoding="utf-8")
    _formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


def _extract_digits(value: str) -> str:
    """Extract and concatenate all digits from the input string."""
    parts = _DIGITS_RE.findall(value)
    digits = "".join(parts)
    if not digits:
        logger.error("No digits found in input: %r", value)
    else:
        logger.debug("Extracted %d digits from input", len(digits))
    return digits


def get_mask_card_number(card_number: str) -> str:
    """Mask card number leaving first 6 and last 4 digits (when possible)."""
    digits = _extract_digits(card_number)
    if not digits:
        logger.error("Cannot mask card number; no digits: %r", card_number)
        return ""

    if len(digits) == 16:
        masked = f"{digits[:4]} {digits[4:6]}** **** {digits[-4:]}"
        logger.debug("Masked 16-digit card number")
        return masked

    if len(digits) <= 8:
        logger.debug("Card number too short to mask fully; returning digits")
        return digits

    head = digits[:4]
    tail = digits[-4:]
    middle_mask = "*" * (len(digits) - 8)
    masked = f"{head}{middle_mask}{tail}"
    logger.debug("Masked card number with variable length: %d", len(digits))
    return masked


def get_mask_account(account: str) -> str:
    """Mask account number leaving only the last 4 digits."""
    digits = _extract_digits(account)
    if not digits:
        logger.error("Cannot mask account number; no digits: %r", account)
        return ""
    masked = f"**{digits[-4:]}"
    logger.debug("Masked account number")
    return masked


def mask_account_number(account_number: str) -> str:
    """Alias for :func:`get_mask_account`."""
    logger.debug("mask_account_number called")
    return get_mask_account(account_number)


def mask_card_number(card_number: str) -> str:
    """Alias for :func:`get_mask_card_number`."""
    logger.debug("mask_card_number called")
    return get_mask_card_number(card_number)
