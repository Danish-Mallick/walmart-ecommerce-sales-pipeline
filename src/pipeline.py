"""Reusable ETL pipeline for the Walmart retail sales portfolio project."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

PathLike = Union[str, Path]
DEFAULT_MIN_WEEKLY_SALES = 10_000

FINAL_COLUMNS = [
    "Store_ID",
    "Month",
    "Dept",
    "IsHoliday",
    "Weekly_Sales",
    "CPI",
    "Unemployment",
]


def extract(store_data: pd.DataFrame, extra_data: PathLike) -> pd.DataFrame:
    """Merge the sales extract with complementary Parquet data.

    The join is validated as one-to-one so duplicate keys fail loudly instead
    of silently multiplying sales rows.
    """
    required_sales_columns = {"index", "Store_ID", "Date", "Dept", "Weekly_Sales"}
    missing = required_sales_columns.difference(store_data.columns)
    if missing:
        raise ValueError(f"store_data is missing required columns: {sorted(missing)}")
    if store_data["index"].duplicated().any():
        raise ValueError("store_data must contain one row per index")

    extra_df = pd.read_parquet(extra_data)
    if "index" not in extra_df.columns:
        raise ValueError("extra_data must contain an 'index' column")
    if extra_df["index"].duplicated().any():
        raise ValueError("extra_data must contain one row per index")

    return store_data.merge(
        extra_df,
        on="index",
        how="inner",
        validate="one_to_one",
        sort=False,
    )


def _fill_numeric_missing_values(data: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric gaps with column medians without mutating the input."""
    result = data.copy()
    numeric_columns = result.select_dtypes(include="number").columns
    for column in numeric_columns:
        if result[column].isna().any():
            median = result[column].median()
            result[column] = result[column].fillna(0 if pd.isna(median) else median)
    return result


def transform(
    merged_df: pd.DataFrame,
    min_weekly_sales: float = DEFAULT_MIN_WEEKLY_SALES,
) -> pd.DataFrame:
    """Clean, filter and project the merged dataset into the curated schema."""
    if min_weekly_sales < 0:
        raise ValueError("min_weekly_sales must be non-negative")

    required_columns = {
        "Store_ID",
        "Date",
        "Dept",
        "IsHoliday",
        "Weekly_Sales",
        "CPI",
        "Unemployment",
    }
    missing = required_columns.difference(merged_df.columns)
    if missing:
        raise ValueError(f"merged_df is missing required columns: {sorted(missing)}")

    data = _fill_numeric_missing_values(merged_df)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"])
    data["Month"] = data["Date"].dt.month.astype("int64")
    data = data.loc[data["Weekly_Sales"] > min_weekly_sales]

    clean_data = data.loc[:, FINAL_COLUMNS].reset_index(drop=True)
    validate_clean_data(clean_data, min_weekly_sales=min_weekly_sales)
    return clean_data


def validate_clean_data(
    clean_data: pd.DataFrame,
    min_weekly_sales: float = DEFAULT_MIN_WEEKLY_SALES,
) -> bool:
    """Enforce the contract of the curated output."""
    if list(clean_data.columns) != FINAL_COLUMNS:
        raise ValueError(
            f"clean_data schema changed: expected {FINAL_COLUMNS}, got {list(clean_data.columns)}"
        )
    if clean_data.isna().any().any():
        raise ValueError("clean_data contains missing values")
    if not clean_data["Month"].between(1, 12).all():
        raise ValueError("clean_data contains an invalid calendar month")
    if not (clean_data["Weekly_Sales"] > min_weekly_sales).all():
        raise ValueError("clean_data contains rows below the configured sales threshold")
    return True


def avg_weekly_sales_per_month(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate average qualifying weekly sales by calendar month."""
    missing = {"Month", "Weekly_Sales"}.difference(clean_data.columns)
    if missing:
        raise ValueError(f"clean_data is missing required columns: {sorted(missing)}")

    return (
        clean_data[["Month", "Weekly_Sales"]]
        .groupby("Month")
        .agg({"Weekly_Sales": "mean"})
        .reset_index()
        .round(2)
    )


def load(
    clean_data: pd.DataFrame,
    clean_data_file_path: PathLike,
    agg_data: pd.DataFrame,
    agg_data_file_path: PathLike,
) -> None:
    """Write curated and aggregate tables as deterministic, index-free CSVs."""
    clean_path = Path(clean_data_file_path)
    agg_path = Path(agg_data_file_path)
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    agg_path.parent.mkdir(parents=True, exist_ok=True)
    clean_data.to_csv(clean_path, index=False)
    agg_data.to_csv(agg_path, index=False)


def validation(file_path: PathLike) -> bool:
    """Return True when a pipeline output exists as a regular file."""
    return Path(file_path).is_file()


def run_pipeline(
    store_data_path: PathLike,
    extra_data_path: PathLike,
    clean_data_path: PathLike,
    agg_data_path: PathLike,
    min_weekly_sales: float = DEFAULT_MIN_WEEKLY_SALES,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run extract -> transform -> validate -> aggregate -> load."""
    store_data = pd.read_csv(store_data_path, parse_dates=["Date"])
    merged_df = extract(store_data, extra_data_path)
    clean_data = transform(merged_df, min_weekly_sales=min_weekly_sales)
    validate_clean_data(clean_data, min_weekly_sales=min_weekly_sales)
    agg_data = avg_weekly_sales_per_month(clean_data)
    load(clean_data, clean_data_path, agg_data, agg_data_path)

    if not validation(clean_data_path) or not validation(agg_data_path):
        raise RuntimeError("Pipeline outputs were not created successfully")

    return clean_data, agg_data
