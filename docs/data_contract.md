# Data contract and quality rules

The repository uses a local sample of the DataCamp sales query plus the complementary Parquet file.

## Source contract

### Sales input

| Column | Rule |
|---|---|
| `index` | unique join key |
| `Store_ID` | required |
| `Date` | parseable date where possible |
| `Dept` | required |
| `Weekly_Sales` | required numeric measure |

### Enrichment input

The Parquet source must contain a unique `index` and the fields required by the curated output, including `IsHoliday`, `CPI` and `Unemployment`.

## Curated contract

`clean_data.csv` contains exactly:

- `Store_ID`
- `Month`
- `Dept`
- `IsHoliday`
- `Weekly_Sales`
- `CPI`
- `Unemployment`

Quality rules:

- no missing values;
- `Month` must be from 1 through 12;
- `Weekly_Sales` must exceed the configured threshold;
- any unexpected schema change fails the run.

## Analytical marts

All marts are derived from `clean_data.csv`.

### month_department_sales.csv

Grain: **department × calendar month**

Measures:

- row count;
- average qualifying weekly sales;
- total qualifying sales.

### department_holiday_sales.csv

Grain: **department**

Measures:

- holiday and regular observation counts;
- holiday and regular average qualifying weekly sales;
- descriptive percentage difference.

### department_sales_summary.csv

Grain: **department**

Measures:

- rank;
- row count;
- average qualifying weekly sales;
- total qualifying sales;
- sales share;
- cumulative sales share.

## Failure behaviour

The ETL layer raises errors for missing source columns, duplicate merge keys, negative thresholds, invalid curated months, missing curated values, schema drift, threshold violations or missing output files.

The marts depend on the curated contract rather than defining a separate cleaning path.
