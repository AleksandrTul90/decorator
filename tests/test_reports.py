from __future__ import annotations

import pandas as pd

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday


def test_spending_by_category_filters(
    sample_operations_df: pd.DataFrame, disable_report_files: None
) -> None:
    out = spending_by_category(sample_operations_df, "Супермаркеты", "2020-05-20")
    assert not out.empty
    assert (out["category"] == "Супермаркеты").all()


def test_spending_by_weekday_shape(
    sample_operations_df: pd.DataFrame, disable_report_files: None
) -> None:
    out = spending_by_weekday(sample_operations_df, "2020-05-20")
    assert "weekday" in out.columns and "average_spending" in out.columns


def test_spending_by_workday_two_rows(
    sample_operations_df: pd.DataFrame, disable_report_files: None
) -> None:
    out = spending_by_workday(sample_operations_df, "2020-05-20")
    types = set(out["day_type"].tolist())
    assert types <= {"weekday", "weekend"}
