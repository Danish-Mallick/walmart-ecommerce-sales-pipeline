"""Downstream analytical marts built only from the curated pipeline output."""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_CLEAN_COLUMNS = {
    "Store_ID",
    "Month",
    "Dept",
    "IsHoliday",
    "Weekly_Sales",
    "CPI",
    "Unemployment",
}


def _validate_input(clean_data: pd.DataFrame) -> None:
    missing = REQUIRED_CLEAN_COLUMNS.difference(clean_data.columns)
    if missing:
        raise ValueError(f"clean_data is missing required columns: {sorted(missing)}")


def month_department_mart(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Return monthly department-level sales measures."""
    _validate_input(clean_data)
    return (
        clean_data.groupby(["Dept", "Month"], as_index=False)
        .agg(
            Rows=("Weekly_Sales", "size"),
            AvgWeeklySales=("Weekly_Sales", "mean"),
            TotalSales=("Weekly_Sales", "sum"),
        )
        .sort_values(["Dept", "Month"])
        .reset_index(drop=True)
        .round({"AvgWeeklySales": 2, "TotalSales": 2})
    )


def department_holiday_mart(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Compare holiday and regular-week averages for every department."""
    _validate_input(clean_data)
    grouped = (
        clean_data.groupby(["Dept", "IsHoliday"], as_index=False)
        .agg(Rows=("Weekly_Sales", "size"), AvgWeeklySales=("Weekly_Sales", "mean"))
    )
    avg = grouped.pivot(index="Dept", columns="IsHoliday", values="AvgWeeklySales")
    cnt = grouped.pivot(index="Dept", columns="IsHoliday", values="Rows")

    result = pd.DataFrame(index=sorted(clean_data["Dept"].unique()))
    result.index.name = "Dept"
    result["HolidayRows"] = cnt.get(1)
    result["RegularRows"] = cnt.get(0)
    result["HolidayAvg"] = avg.get(1)
    result["RegularAvg"] = avg.get(0)
    result["UpliftPct"] = np.where(
        result["HolidayAvg"].notna() & result["RegularAvg"].notna(),
        (result["HolidayAvg"] / result["RegularAvg"] - 1) * 100,
        np.nan,
    )
    return result.reset_index().round(2)


def department_sales_summary(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Rank departments and calculate contribution / cumulative contribution."""
    _validate_input(clean_data)
    out = (
        clean_data.groupby("Dept", as_index=False)
        .agg(
            Rows=("Weekly_Sales", "size"),
            AvgWeeklySales=("Weekly_Sales", "mean"),
            TotalSales=("Weekly_Sales", "sum"),
        )
        .sort_values("TotalSales", ascending=False)
        .reset_index(drop=True)
    )
    out.insert(0, "Rank", np.arange(1, len(out) + 1))
    total = out["TotalSales"].sum()
    out["SalesSharePct"] = out["TotalSales"] / total * 100
    out["CumulativeSharePct"] = out["SalesSharePct"].cumsum()
    return out.round(2)
