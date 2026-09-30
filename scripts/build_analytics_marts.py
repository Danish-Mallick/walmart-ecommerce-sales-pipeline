"""Build analytical marts from the trusted clean_data.csv output."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analytics import (  # noqa: E402
    department_holiday_mart,
    department_sales_summary,
    month_department_mart,
)


def main() -> None:
    source = ROOT / "data/processed/clean_data.csv"
    output = ROOT / "data/marts"
    output.mkdir(parents=True, exist_ok=True)

    clean = pd.read_csv(source)

    marts = {
        "month_department_sales.csv": month_department_mart(clean),
        "department_holiday_sales.csv": department_holiday_mart(clean),
        "department_sales_summary.csv": department_sales_summary(clean),
    }

    for name, frame in marts.items():
        path = output / name
        frame.to_csv(path, index=False)
        print(f"{name}: {len(frame):,} rows -> {path}")


if __name__ == "__main__":
    main()
