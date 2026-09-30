# Data contract and quality rules

The local repository uses a sample of the DataCamp sales query plus the complementary Parquet file. This document makes the expected inputs and outputs explicit.

## Sales input

Required columns:

| Column | Purpose |
|---|---|
| `index` | Join key; must be unique |
| `Store_ID` | Store identifier |
| `Date` | Weekly observation date |
| `Dept` | Department identifier |
| `Weekly_Sales` | Weekly sales value |

## Enrichment input

The Parquet dataset must contain a unique `index` plus the fields required by the curated output:

- `IsHoliday`
- `CPI`
- `Unemployment`

The source also contains fields such as temperature, fuel price, markdown values, store type and store size. They remain available in the merged intermediate dataframe but are not part of the current curated contract.

## Curated output

`clean_data.csv` contains exactly:

| Column | Rule |
|---|---|
| `Store_ID` | required |
| `Month` | integer from 1 to 12 |
| `Dept` | required |
| `IsHoliday` | required |
| `Weekly_Sales` | strictly above the configured threshold |
| `CPI` | non-null after numeric imputation |
| `Unemployment` | non-null after numeric imputation |

## Aggregate output

`agg_data.csv` contains:

- `Month`
- average qualifying `Weekly_Sales`, rounded to two decimals.

## Failure behaviour

The pipeline raises an error when:

- required source columns are missing;
- either join input contains duplicate `index` values;
- the configured threshold is negative;
- the curated schema changes unexpectedly;
- curated data contains missing values;
- an invalid month survives transformation;
- a row violates the sales threshold;
- expected output files are not created.

These are deliberately explicit quality gates. In a larger platform they could be implemented in a data-quality framework, but keeping them in plain Python makes the portfolio project easy to inspect and run.
