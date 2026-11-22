
import duckdb
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

# Connect to DuckDB
con = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Get each customer's first delivered order month
query = """
WITH delivered_orders AS (
    SELECT
        customer_id,
        CAST(order_date AS DATE) AS order_date,
        DATE_TRUNC('month', CAST(order_date AS DATE)) AS order_month
    FROM orders
    WHERE order_status = 'Delivered'
),

customer_cohorts AS (
    SELECT
        customer_id,
        MIN(order_month) AS cohort_month
    FROM delivered_orders
    GROUP BY customer_id
),

customer_activity AS (
    SELECT DISTINCT
        d.customer_id,
        c.cohort_month,
        d.order_month,
        DATE_DIFF(
            'month',
            c.cohort_month,
            d.order_month
        ) AS cohort_index
    FROM delivered_orders d
    JOIN customer_cohorts c
        ON d.customer_id = c.customer_id
)

SELECT
    cohort_month,
    cohort_index,
    COUNT(DISTINCT customer_id) AS active_customers
FROM customer_activity
GROUP BY cohort_month, cohort_index
ORDER BY cohort_month, cohort_index
"""

cohort_data = con.execute(query).df()

# 2. Create cohort retention matrix
cohort_pivot = cohort_data.pivot(
    index="cohort_month",
    columns="cohort_index",
    values="active_customers"
)

# 3. Calculate original cohort size
cohort_sizes = cohort_pivot[0]

# 4. Calculate retention percentages
retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100

# 5. Save reports
cohort_data.to_csv(
    REPORT_DIR / "customer_cohort_data.csv",
    index=False
)

cohort_pivot.to_csv(
    REPORT_DIR / "customer_cohort_counts.csv"
)

retention.to_csv(
    REPORT_DIR / "customer_retention_matrix.csv"
)

# 6. Display results
print("\n========== CUSTOMER COHORT ANALYSIS ==========")

print("\nCohort customer counts:")
print(cohort_pivot.fillna(0).round(0))

print("\nCustomer retention matrix (%):")
print(retention.round(2))

print("\n========== FIRST MONTH SUMMARY ==========")

summary = pd.DataFrame({
    "cohort_customers": cohort_sizes,
    "month_1_retention_percent": retention[1]
        if 1 in retention.columns else None,
    "month_2_retention_percent": retention[2]
        if 2 in retention.columns else None
})

print(summary.round(2))

print("\nReports saved successfully in the reports folder.")

con.close()
