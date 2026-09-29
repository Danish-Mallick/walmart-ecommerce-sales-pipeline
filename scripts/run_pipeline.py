"""Run the local Walmart e-commerce ETL pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sales",
        type=Path,
        default=ROOT / "data/raw/grocery_sales_sample.csv",
        help="Local grocery sales CSV extract.",
    )
    parser.add_argument(
        "--extra-data",
        type=Path,
        default=ROOT / "data/raw/extra_data.parquet",
        help="Complementary Parquet file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data/processed",
        help="Directory for clean_data.csv and agg_data.csv.",
    )
    args = parser.parse_args()

    clean_path = args.output_dir / "clean_data.csv"
    agg_path = args.output_dir / "agg_data.csv"
    clean_data, agg_data = run_pipeline(
        args.sales, args.extra_data, clean_path, agg_path
    )

    print(f"Merged and transformed rows: {len(clean_data):,}")
    print(f"Clean output: {clean_path}")
    print(f"Aggregate output: {agg_path}")
    print("\nAverage weekly sales by month:")
    print(agg_data.to_string(index=False))


if __name__ == "__main__":
    main()
