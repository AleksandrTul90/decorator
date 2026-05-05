from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.utils import filter_successful, normalize_transactions_dataframe


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_operations_df(project_root: Path) -> pd.DataFrame:
    """Таблица операций для тестов (соответствует выгрузке Т-Банка)."""
    p = project_root / "data" / "operations.xlsx"
    assert p.is_file(), f"Создайте файл данных: {p}"
    df = pd.read_excel(p)
    df = normalize_transactions_dataframe(df)
    return filter_successful(df)


@pytest.fixture
def disable_report_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Не оставлять report-файлы в корне репозитория при тестах."""

    def _noop(path: Path, result: object) -> None:
        _ = (path, result)

    monkeypatch.setattr("src.reports._write_report_result", _noop)
