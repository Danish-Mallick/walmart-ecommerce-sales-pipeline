# Data provenance

The Parquet file is the complementary dataset supplied with the DataCamp
assignment. The notebook's SQL output was exported into
`grocery_sales_sample.csv` so the repository can be run without a PostgreSQL
connection.

The original course SQL query is preserved in `sql/grocery_sales.sql`. In the
DataCamp workspace it returns the complete `grocery_sales` table. The local CSV
is the row sample preserved in the uploaded notebook export, so the local run
is reproducible but should not be presented as a complete Walmart production
dataset. Replace it with a full SQL export when performing a full-scale study.
