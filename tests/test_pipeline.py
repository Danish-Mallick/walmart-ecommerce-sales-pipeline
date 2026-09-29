from pathlib import Path

import pandas as pd

from src.pipeline import (
    FINAL_COLUMNS,
    avg_weekly_sales_per_month,
    load,
    transform,
    validation,
)


def sample_merged_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "index": [1, 2, 3],
            "Store_ID": [1, 1, 2],
            "Date": ["2011-01-07", "2011-02-04", "not-a-date"],
            "Dept": [1, 2, 3],
            "Weekly_Sales": [12_000.0, 8_000.0, 15_000.0],
            "IsHoliday": [0, 1, 0],
            "CPI": [210.0, None, 215.0],
            "Unemployment": [8.0, 7.5, None],
            "Temperature": [50.0, 42.0, 38.0],
        }
    )


def test_transform_fills_values_filters_sales_and_keeps_schema():
    clean = transform(sample_merged_data())

    assert list(clean.columns) == FINAL_COLUMNS
    assert len(clean) == 1
    assert clean.iloc[0]["Month"] == 1
    assert clean.isna().sum().sum() == 0


def test_monthly_aggregation_uses_only_required_columns():
    clean = pd.DataFrame(
        {
            "Month": [1, 1, 2],
            "Weekly_Sales": [10_001, 20_001, 30_001],
            "unrelated": ["a", "b", "c"],
        }
    )

    aggregate = avg_weekly_sales_per_month(clean)

    assert aggregate.to_dict("records") == [
        {"Month": 1, "Weekly_Sales": 15001.0},
        {"Month": 2, "Weekly_Sales": 30001.0},
    ]


def test_load_writes_index_free_csv_and_validation(tmp_path: Path):
    clean_path = tmp_path / "nested" / "clean_data.csv"
    aggregate_path = tmp_path / "nested" / "agg_data.csv"
    clean = pd.DataFrame({"Store_ID": [1], "Weekly_Sales": [12_000]})
    aggregate = pd.DataFrame({"Month": [1], "Weekly_Sales": [12_000.0]})

    load(clean, clean_path, aggregate, aggregate_path)

    assert validation(clean_path)
    assert validation(aggregate_path)
    assert "Unnamed: 0" not in pd.read_csv(clean_path).columns
