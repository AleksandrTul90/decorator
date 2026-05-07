from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src import main


def test_main_runs_with_sample_data(
    sample_operations_df: pd.DataFrame,
    disable_report_files: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    main.main(
        data_path=Path("dummy.xlsx"),
        load_operations=lambda _: sample_operations_df,
    )
    out = capsys.readouterr().out
    assert "Веб-страницы: JSON «Главная»" in out
    assert "Веб-страницы: JSON «События»" in out
    assert "Сервисы: кешбэк по категориям" in out
    assert "Отчёты: траты по категории" in out
