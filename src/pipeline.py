"""Extract, transform, aggregate, load, and validate the retail dataset.

The functions are intentionally small and composable so the same logic can be
used from the notebook, a command-line run, or an automated test.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

PathLike = Union[str, Path]

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
    """Merge the sales table with the complementary Parquet data.

    Parameters
    ----------
    store_data:
        Sales data returned by the SQL query or loaded from the local CSV
        extract. It must contain a unique ``index`` column.
    extra_data:
        Path to ``extra_data.parquet``.
    """

    required_sales_columns = {"index", "Store_ID", "Date", "Dept", "Weekly_Sales"}
    missing = required_sales_columns.difference(store_data.columns)
    if missing:
        raise ValueError(f"store_data is missing required columns: {sorted(missing)}")

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
            # A completely empty numeric column has no meaningful median.
            result[column] = result[column].fillna(0 if pd.isna(median) else median)
    return result


def transform(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Clean the merged data and return the analysis-ready dataset.

    The transformation follows the assignment requirements: numerical gaps
    are filled, a numeric month is derived from ``Date``, low-sales rows are
    removed, and only the business-ready columns are retained.
    """

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
    data = data.loc[data["Weekly_Sales"] > 10_000]

    return data.loc[:, FINAL_COLUMNS].reset_index(drop=True)


def avg_weekly_sales_per_month(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate average weekly sales by calendar month, rounded to 2 decimals."""

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
    """Write the cleaned and aggregated tables as index-free CSV files."""

    clean_path = Path(clean_data_file_path)
    agg_path = Path(agg_data_file_path)
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    agg_path.parent.mkdir(parents=True, exist_ok=True)
    clean_data.to_csv(clean_path, index=False)
    agg_data.to_csv(agg_path, index=False)


def validation(file_path: PathLike) -> bool:
    """Return ``True`` when a pipeline output exists as a regular file."""

    return Path(file_path).is_file()


def run_pipeline(
    store_data_path: PathLike,
    extra_data_path: PathLike,
    clean_data_path: PathLike,
    agg_data_path: PathLike,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the complete local pipeline and return both output DataFrames."""

    store_data = pd.read_csv(store_data_path, parse_dates=["Date"])
    merged_df = extract(store_data, extra_data_path)
    clean_data = transform(merged_df)
    agg_data = avg_weekly_sales_per_month(clean_data)
    load(clean_data, clean_data_path, agg_data, agg_data_path)

    if not validation(clean_data_path) or not validation(agg_data_path):
        raise RuntimeError("Pipeline outputs were not created successfully")

    return clean_data, agg_data
