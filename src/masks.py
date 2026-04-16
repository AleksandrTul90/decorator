from __future__ import annotations

import re

_DIGITS_RE = re.compile(r"\d+")


def _extract_digits(value: str) -> str:
    parts = _DIGITS_RE.findall(value)
    return "".join(parts)


def get_mask_card_number(card_number: str) -> str:
    digits = _extract_digits(card_number)
    if not digits:
        return ""

    if len(digits) == 16:
        return f"{digits[:4]} {digits[4:6]}** **** {digits[-4:]}"

    if len(digits) <= 8:
        return digits

    head = digits[:4]
    tail = digits[-4:]
    middle_mask = "*" * (len(digits) - 8)
    return f"{head}{middle_mask}{tail}"


def get_mask_account(account: str) -> str:
    digits = _extract_digits(account)
    if not digits:
        return ""
    return f"**{digits[-4:]}"


def mask_account_number(account_number: str) -> str:
    return get_mask_account(account_number)


def mask_card_number(card_number: str) -> str:
    return get_mask_card_number(card_number)

