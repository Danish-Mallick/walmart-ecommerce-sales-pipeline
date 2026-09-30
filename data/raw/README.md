# Source data note

This repository does not claim ownership of the underlying Walmart retail dataset.

The local project contains a **20,000-row sales extract** plus a complementary Parquet dataset so the pipeline can be executed without external database credentials. The full source extract is not included here.

The SQL used to retrieve the sales table is preserved in `sql/grocery_sales.sql`.

The pipeline, validation rules, analytical marts, tests, CI workflow and visual analysis in this repository operate on those supplied source files.
