"""Create portfolio-ready summary tables and charts from pipeline outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def create_analysis(clean_path: Path, aggregate_path: Path, report_dir: Path) -> dict[str, float]:
    clean = pd.read_csv(clean_path)
    aggregate = pd.read_csv(aggregate_path)
    report_dir.mkdir(parents=True, exist_ok=True)

    quality_report = pd.DataFrame(
        {
            "column": clean.columns,
            "dtype": [str(dtype) for dtype in clean.dtypes],
            "missing_values": clean.isna().sum().to_numpy(),
            "missing_percent": (clean.isna().mean().mul(100).round(2)).to_numpy(),
            "unique_values": clean.nunique(dropna=True).to_numpy(),
        }
    )
    quality_report.to_csv(report_dir / "data_quality_report.csv", index=False)

    sns.set_theme(style="whitegrid", palette="colorblind")
    accent = "#0F766E"
    gold = "#D97706"
    navy = "#16324F"

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.lineplot(data=aggregate, x="Month", y="Weekly_Sales", marker="o", color=accent, ax=ax)
    ax.set_title("Average weekly sales by calendar month", loc="left", weight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average weekly sales ($)")
    ax.set_xticks(sorted(aggregate["Month"].unique()))
    fig.tight_layout()
    fig.savefig(report_dir / "monthly_sales_trend.png", dpi=180)
    plt.close(fig)

    holiday_summary = (
        clean.groupby("IsHoliday", as_index=False)["Weekly_Sales"]
        .mean()
        .assign(Period=lambda x: x["IsHoliday"].map({0: "Regular week", 1: "Holiday week"}))
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(
        data=holiday_summary,
        x="Period",
        y="Weekly_Sales",
        hue="Period",
        palette=[navy, gold],
        legend=False,
        ax=ax,
    )
    ax.set_title("Average weekly sales: holiday vs. regular weeks", loc="left", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Average weekly sales ($)")
    fig.tight_layout()
    fig.savefig(report_dir / "holiday_sales_comparison.png", dpi=180)
    plt.close(fig)

    top_stores = (
        clean.groupby("Store_ID", as_index=False)["Weekly_Sales"]
        .mean()
        .sort_values("Weekly_Sales", ascending=False)
        .head(10)
    )
    top_stores_plot = top_stores.assign(Store=top_stores["Store_ID"].astype(str))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=top_stores_plot,
        y="Store",
        x="Weekly_Sales",
        orient="h",
        color=accent,
        ax=ax,
    )
    ax.set_title("Top stores by average qualifying weekly sales", loc="left", weight="bold")
    ax.set_xlabel("Average weekly sales ($)")
    ax.set_ylabel("Store ID")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(report_dir / "top_store_sales.png", dpi=180)
    plt.close(fig)

    holiday_lookup = holiday_summary.set_index("IsHoliday")["Weekly_Sales"]
    holiday_lift = float(
        (holiday_lookup.get(1, float("nan")) / holiday_lookup.get(0, float("nan")) - 1) * 100
    )
    peak_row = aggregate.loc[aggregate["Weekly_Sales"].idxmax()]
    summary = {
        "rows_after_filter": int(len(clean)),
        "stores_after_filter": int(clean["Store_ID"].nunique()),
        "departments_after_filter": int(clean["Dept"].nunique()),
        "peak_month": int(peak_row["Month"]),
        "peak_month_average_sales": float(peak_row["Weekly_Sales"]),
        "holiday_lift_percent": holiday_lift,
    }
    pd.DataFrame([summary]).to_csv(report_dir / "analysis_summary.csv", index=False)
    holiday_summary.to_csv(report_dir / "holiday_summary.csv", index=False)
    top_stores.to_csv(report_dir / "top_stores.csv", index=False)
    return summary


if __name__ == "__main__":
    result = create_analysis(
        ROOT / "data/processed/clean_data.csv",
        ROOT / "data/processed/agg_data.csv",
        ROOT / "reports",
    )
    for key, value in result.items():
        print(f"{key}: {value}")
