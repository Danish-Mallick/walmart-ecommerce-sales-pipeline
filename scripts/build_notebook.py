"""Build the reproducible portfolio notebook from the reusable pipeline code."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/grocery_sales_pipeline.ipynb"


def build_notebook() -> None:
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    }
    notebook["cells"] = [
        nbf.v4.new_markdown_cell(
            """# Walmart E-commerce Sales Pipeline

This notebook demonstrates a small, testable ETL workflow for Walmart weekly sales. I use the supplied DataCamp inputs, keep the transformation logic in `src/pipeline.py`, and use the notebook for exploration and communication.

The original course workflow runs `SELECT * FROM grocery_sales` in a PostgreSQL-backed SQL cell. For a reproducible local run, this notebook uses the exported local sample in `data/raw/grocery_sales_sample.csv`. Replace that file with the full SQL export when running a full-scale analysis."""
        ),
        nbf.v4.new_code_cell(
            """from pathlib import Path\nimport sys\n\nimport pandas as pd\nimport seaborn as sns\nimport matplotlib.pyplot as plt\n\nROOT = Path.cwd()\nif not (ROOT / "src").exists():\n    ROOT = Path.cwd().parent\nsys.path.insert(0, str(ROOT))\n\nfrom src.pipeline import (\n    extract,\n    transform,\n    avg_weekly_sales_per_month,\n    load,\n    validation,\n)\n\nSALES_PATH = ROOT / "data/raw/grocery_sales_sample.csv"\nEXTRA_DATA_PATH = ROOT / "data/raw/extra_data.parquet"\nCLEAN_PATH = ROOT / "data/processed/clean_data.csv"\nAGG_PATH = ROOT / "data/processed/agg_data.csv"\nREPORT_PATH = ROOT / "reports"\nREPORT_PATH.mkdir(exist_ok=True)"""
        ),
        nbf.v4.new_markdown_cell("## 1. Extract and merge the two sources"),
        nbf.v4.new_code_cell(
            """store_data = pd.read_csv(SALES_PATH, parse_dates=["Date"])\nmerged_df = extract(store_data, EXTRA_DATA_PATH)\nprint(f"Sales rows: {len(store_data):,}")\nprint(f"Merged rows: {len(merged_df):,}")\nmerged_df.head()"""
        ),
        nbf.v4.new_markdown_cell(
            """## 2. Transform\n\nThe transformation fills missing numeric values with column medians, converts the sales date to a calendar month, removes rows at or below the `$10,000` threshold, and retains the seven columns needed for downstream analysis."""
        ),
        nbf.v4.new_code_cell(
            """clean_data = transform(merged_df)\nprint(f"Rows after the > $10,000 filter: {len(clean_data):,}")\nprint(f"Remaining missing values: {int(clean_data.isna().sum().sum())}")\nclean_data.head()"""
        ),
        nbf.v4.new_markdown_cell("## 3. Aggregate monthly sales"),
        nbf.v4.new_code_cell(
            """agg_data = avg_weekly_sales_per_month(clean_data)\nagg_data"""
        ),
        nbf.v4.new_markdown_cell("## 4. Load and validate the outputs"),
        nbf.v4.new_code_cell(
            """load(clean_data, CLEAN_PATH, agg_data, AGG_PATH)\nprint({\n    "clean_data.csv": validation(CLEAN_PATH),\n    "agg_data.csv": validation(AGG_PATH),\n})"""
        ),
        nbf.v4.new_markdown_cell("## 5. Preliminary business analysis"),
        nbf.v4.new_code_cell(
            """sns.set_theme(style="whitegrid", palette="colorblind")\nfig, ax = plt.subplots(figsize=(10, 5))\nsns.lineplot(data=agg_data, x="Month", y="Weekly_Sales", marker="o", color="#0F766E", ax=ax)\nax.set_title("Average weekly sales by calendar month", loc="left", weight="bold")\nax.set_xlabel("Month")\nax.set_ylabel("Average weekly sales ($)")\nplt.tight_layout()\nplt.show()"""
        ),
        nbf.v4.new_code_cell(
            """holiday_summary = (\n    clean_data.groupby("IsHoliday", as_index=False)["Weekly_Sales"]\n    .mean()\n    .assign(Period=lambda x: x["IsHoliday"].map({0: "Regular week", 1: "Holiday week"}))\n)\nholiday_summary"""
        ),
        nbf.v4.new_code_cell(
            """holiday_values = holiday_summary.set_index("IsHoliday")["Weekly_Sales"]\nholiday_lift = (holiday_values[1] / holiday_values[0] - 1) * 100\npeak_month = int(agg_data.loc[agg_data["Weekly_Sales"].idxmax(), "Month"])\nprint(f"Peak month in this local extract: {peak_month}")\nprint(f"Holiday-week average sales lift: {holiday_lift:.1f}%")\nprint("\nThese are descriptive results, not causal estimates. The holiday flag is not a controlled experiment, and the local CSV is a sample rather than the full SQL extract.")"""
        ),
        nbf.v4.new_markdown_cell(
            """## Interpretation and next steps\n\nThe monthly table is useful for an initial planning conversation, but it should not be used alone to set inventory levels. A stronger version would use the complete SQL extract, separate stores and departments, compare like-for-like weeks, and control for promotions, store size, CPI, and unemployment. A natural next step would be a holiday-lift model or a demand forecast with a proper time-based validation split."""
        ),
    ]
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NOTEBOOK_PATH.open("w", encoding="utf-8") as file:
        nbf.write(notebook, file)
    print(f"Built {NOTEBOOK_PATH}")


if __name__ == "__main__":
    build_notebook()
