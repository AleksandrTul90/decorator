from __future__ import annotations

import re
from pathlib import Path

import pytest

from decorators import log


def test_log_to_console_success(capsys: pytest.CaptureFixture[str]) -> None:
    @log()
    def add(a: int, b: int) -> int:
        """Return sum."""

        return a + b

    assert add(2, 3) == 5

    out = capsys.readouterr().out
    assert "CALL add" in out
    assert "args=(2, 3)" in out
    assert "kwargs={}" in out
    assert "RESULT add -> 5" in out


def test_log_to_console_error(capsys: pytest.CaptureFixture[str]) -> None:
    @log()
    def boom(x: int) -> int:
        """Always raise."""

        raise ValueError("bad")

    with pytest.raises(ValueError):
        boom(7)

    out = capsys.readouterr().out
    assert "CALL boom" in out
    assert "ERROR boom ValueError" in out
    assert "args=(7,)" in out


def test_log_to_file_success(tmp_path: Path) -> None:
    log_file = tmp_path / "app.log"

    @log(filename=str(log_file))
    def mul(a: int, b: int) -> int:
        """Return product."""

        return a * b

    assert mul(3, 4) == 12

    text = log_file.read_text(encoding="utf-8")
    assert "CALL mul" in text
    assert "RESULT mul -> 12" in text


def test_log_timestamp_present_in_lines(capsys: pytest.CaptureFixture[str]) -> None:
    @log()
    def f() -> str:
        """Return constant string."""

        return "ok"

    assert f() == "ok"
    out_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(out_lines) >= 2

    # Expect ISO-like timestamp between brackets: [2026-...]
    assert re.search(r"^\[\d{4}-\d{2}-\d{2}T", out_lines[0]) is not None
