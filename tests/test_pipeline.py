from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import (
    FINAL_COLUMNS,
    avg_weekly_sales_per_month,
    extract,
    load,
    run_pipeline,
    transform,
    validate_clean_data,
    validation,
)


def sample_sales() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "index": [1, 2, 3],
            "Store_ID": [1, 1, 2],
            "Date": ["2011-01-07", "2011-02-04", "2011-03-04"],
            "Dept": [1, 2, 3],
            "Weekly_Sales": [12_000.0, 8_000.0, 15_000.0],
        }
    )


def sample_extra() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "index": [1, 2, 3],
            "IsHoliday": [0, 1, 0],
            "CPI": [210.0, None, 215.0],
            "Unemployment": [8.0, 7.5, None],
            "Temperature": [50.0, 42.0, 38.0],
        }
    )


def test_extract_performs_one_to_one_merge(tmp_path: Path):
    extra_path = tmp_path / "extra.parquet"
    sample_extra().to_parquet(extra_path, index=False)
    merged = extract(sample_sales(), extra_path)
    assert len(merged) == 3
    assert {"IsHoliday", "CPI", "Unemployment"}.issubset(merged.columns)


def test_extract_rejects_duplicate_enrichment_keys(tmp_path: Path):
    extra = pd.concat([sample_extra(), sample_extra().iloc[[0]]], ignore_index=True)
    extra_path = tmp_path / "duplicate_extra.parquet"
    extra.to_parquet(extra_path, index=False)
    with pytest.raises(ValueError, match="one row per index"):
        extract(sample_sales(), extra_path)


def test_extract_rejects_duplicate_sales_keys(tmp_path: Path):
    sales = pd.concat([sample_sales(), sample_sales().iloc[[0]]], ignore_index=True)
    extra_path = tmp_path / "extra.parquet"
    sample_extra().to_parquet(extra_path, index=False)
    with pytest.raises(ValueError, match="store_data must contain one row per index"):
        extract(sales, extra_path)


def test_transform_imputes_filters_and_keeps_schema():
    merged = sample_sales().merge(sample_extra(), on="index")
    merged.loc[2, "Date"] = "not-a-date"
    clean = transform(merged)
    assert list(clean.columns) == FINAL_COLUMNS
    assert len(clean) == 1
    assert clean.iloc[0]["Month"] == 1
    assert clean.isna().sum().sum() == 0


def test_transform_supports_configurable_threshold():
    merged = sample_sales().merge(sample_extra(), on="index")
    clean = transform(merged, min_weekly_sales=7_500)
    assert len(clean) == 3
    assert clean["Weekly_Sales"].min() > 7_500


def test_validate_clean_data_rejects_contract_violation():
    invalid = pd.DataFrame(
        {
            "Store_ID": [1],
            "Month": [13],
            "Dept": [1],
            "IsHoliday": [0],
            "Weekly_Sales": [12_000.0],
            "CPI": [210.0],
            "Unemployment": [8.0],
        }
    )
    with pytest.raises(ValueError, match="invalid calendar month"):
        validate_clean_data(invalid)


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


def test_run_pipeline_end_to_end(tmp_path: Path):
    sales_path = tmp_path / "sales.csv"
    extra_path = tmp_path / "extra.parquet"
    clean_path = tmp_path / "out" / "clean.csv"
    agg_path = tmp_path / "out" / "agg.csv"

    sample_sales().to_csv(sales_path, index=False)
    sample_extra().to_parquet(extra_path, index=False)

    clean, aggregate = run_pipeline(sales_path, extra_path, clean_path, agg_path)

    assert clean_path.is_file()
    assert agg_path.is_file()
    assert len(clean) == 2
    assert aggregate["Month"].tolist() == [1, 3]
