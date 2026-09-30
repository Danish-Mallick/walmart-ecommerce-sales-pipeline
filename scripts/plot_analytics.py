"""Create professional analytical figures from curated marts using Seaborn."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data/marts"
REPORTS = ROOT / "reports"

NAVY = "#10263F"
TEAL = "#0F766E"
BLUE = "#2563EB"
AMBER = "#D97706"
CORAL = "#C2410C"
MUTED = "#64748B"
BG = "#F7F9FC"


def _base():
    sns.set_theme(
        style="whitegrid",
        font_scale=1.0,
        rc={
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": "#DCE5EE",
            "grid.color": "#DCE5EE",
            "axes.labelcolor": NAVY,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": NAVY,
        },
    )


def plot_monthly(clean: pd.DataFrame) -> None:
    monthly = clean.groupby("Month", as_index=False)["Weekly_Sales"].mean()
    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.lineplot(data=monthly, x="Month", y="Weekly_Sales", marker="o", linewidth=3, color=BLUE, ax=ax)
    ax.scatter(monthly.loc[monthly.Month >= 11, "Month"], monthly.loc[monthly.Month >= 11, "Weekly_Sales"], s=90, color=AMBER, zorder=5)
    ax.set_title("When are qualifying weekly sales strongest?", loc="left", weight="bold", fontsize=18)
    ax.text(0, 1.02, "November and December stand out after the pipeline's > $10,000 filter.", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Average qualifying weekly sales ($)")
    ax.set_xticks(range(1, 13))
    sns.despine()
    fig.tight_layout()
    fig.savefig(REPORTS / "monthly_sales_story.svg", bbox_inches="tight")
    plt.close(fig)


def plot_top_departments(summary: pd.DataFrame) -> None:
    top = summary.head(10).sort_values("TotalSales")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    sns.barplot(data=top, y=top["Dept"].astype(str), x="TotalSales", color=TEAL, ax=ax)
    ax.set_title("Which departments contribute the most qualifying sales?", loc="left", weight="bold", fontsize=18)
    ax.text(0, 1.02, "Top 10 departments by total sales in the filtered sample.", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Total qualifying sales ($)")
    ax.set_ylabel("Department")
    sns.despine()
    fig.tight_layout()
    fig.savefig(REPORTS / "top_departments.svg", bbox_inches="tight")
    plt.close(fig)


def plot_holiday_uplift(holiday: pd.DataFrame) -> None:
    eligible = holiday.query("HolidayRows >= 5 and RegularRows >= 20").dropna(subset=["UpliftPct"])
    chosen = pd.concat([eligible.nlargest(6, "UpliftPct"), eligible.nsmallest(6, "UpliftPct")]).drop_duplicates()
    chosen = chosen.sort_values("UpliftPct")
    palette = [CORAL if v < 0 else TEAL for v in chosen["UpliftPct"]]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(chosen["Dept"].astype(str), chosen["UpliftPct"], color=palette)
    ax.axvline(0, color=NAVY, linewidth=1.2)
    ax.set_title("Is the holiday difference spread evenly across departments?", loc="left", weight="bold", fontsize=18)
    ax.text(0, 1.02, "Department-level holiday differences vary sharply; this is descriptive, not causal.", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Holiday vs regular-week average difference (%)")
    ax.set_ylabel("Department")
    sns.despine()
    fig.tight_layout()
    fig.savefig(REPORTS / "holiday_uplift_by_department.svg", bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(month_department: pd.DataFrame, summary: pd.DataFrame) -> None:
    top_ids = summary.head(12)["Dept"]
    matrix = (
        month_department[month_department["Dept"].isin(top_ids)]
        .pivot(index="Dept", columns="Month", values="AvgWeeklySales")
        .reindex(top_ids)
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(matrix, cmap="crest", linewidths=.5, linecolor=BG, cbar_kws={"label": "Avg qualifying weekly sales ($)"}, ax=ax)
    ax.set_title("Where do department-level seasonal patterns appear?", loc="left", weight="bold", fontsize=18)
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Department")
    fig.tight_layout()
    fig.savefig(REPORTS / "department_month_heatmap.svg", bbox_inches="tight")
    plt.close(fig)


def plot_concentration(summary: pd.DataFrame) -> None:
    top = summary.head(15)
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=top, x=top["Dept"].astype(str), y="SalesSharePct", color=TEAL, ax=ax)
    ax2 = ax.twinx()
    ax2.plot(range(len(top)), top["CumulativeSharePct"], color=AMBER, linewidth=3, marker="o")
    ax.set_title("How concentrated are qualifying sales across departments?", loc="left", weight="bold", fontsize=18)
    ax.set_xlabel("Department")
    ax.set_ylabel("Share of qualifying sales (%)")
    ax2.set_ylabel("Cumulative share (%)", color=AMBER)
    ax2.grid(False)
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(REPORTS / "department_sales_concentration.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    _base()
    clean = pd.read_csv(ROOT / "data/processed/clean_data.csv")
    month_department = pd.read_csv(MARTS / "month_department_sales.csv")
    holiday = pd.read_csv(MARTS / "department_holiday_sales.csv")
    summary = pd.read_csv(MARTS / "department_sales_summary.csv")

    plot_monthly(clean)
    plot_top_departments(summary)
    plot_holiday_uplift(holiday)
    plot_heatmap(month_department, summary)
    plot_concentration(summary)


if __name__ == "__main__":
    main()
