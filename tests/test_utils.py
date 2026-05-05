from __future__ import annotations

from datetime import datetime

import pytest

from src.utils import greeting_for_datetime


@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (5, "Доброй ночи"),
    ],
)
def test_greeting_intervals(hour: int, expected: str) -> None:
    dt = datetime(2020, 5, 20, hour, 0, 0)
    assert greeting_for_datetime(dt) == expected
