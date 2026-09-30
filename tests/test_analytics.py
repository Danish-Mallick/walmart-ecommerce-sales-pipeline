import pandas as pd

from src.analytics import (
    department_holiday_mart,
    department_sales_summary,
    month_department_mart,
)


def clean_sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Store_ID": [1, 1, 1, 1, 1],
            "Month": [1, 1, 2, 2, 2],
            "Dept": [1, 1, 1, 2, 2],
            "IsHoliday": [0, 1, 0, 0, 1],
            "Weekly_Sales": [100.0, 120.0, 140.0, 50.0, 100.0],
            "CPI": [200.0] * 5,
            "Unemployment": [8.0] * 5,
        }
    )


def test_month_department_mart_has_expected_grain():
    mart = month_department_mart(clean_sample())
    assert set(mart.columns) == {"Dept", "Month", "Rows", "AvgWeeklySales", "TotalSales"}
    assert len(mart) == 3


def test_department_holiday_mart_calculates_uplift():
    mart = department_holiday_mart(clean_sample()).set_index("Dept")
    assert mart.loc[2, "HolidayAvg"] == 100.0
    assert mart.loc[2, "RegularAvg"] == 50.0
    assert mart.loc[2, "UpliftPct"] == 100.0


def test_department_sales_summary_is_ranked_and_cumulative():
    summary = department_sales_summary(clean_sample())
    assert summary.iloc[0]["Rank"] == 1
    assert summary["CumulativeSharePct"].is_monotonic_increasing
    assert round(summary.iloc[-1]["CumulativeSharePct"], 2) == 100.0
