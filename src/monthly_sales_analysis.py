
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

conn = duckdb.connect(str(DB_PATH), read_only=True)

query = """
WITH monthly_orders AS (
    SELECT
        DATE_TRUNC('month', CAST(order_date AS DATE)) AS sales_month,
        COUNT(*) AS total_orders,
        SUM(final_amount) AS order_value

    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY 1
),

monthly_products AS (
    SELECT
        DATE_TRUNC('month', CAST(o.order_date AS DATE)) AS sales_month,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.profit) AS product_profit

    FROM orders o

    JOIN order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'Delivered'
    GROUP BY 1
)

SELECT
    m.sales_month,
    m.total_orders,
    ROUND(m.order_value, 2) AS order_value_inr,
    ROUND(p.product_revenue, 2) AS product_revenue_inr,
    ROUND(p.product_profit, 2) AS product_profit_inr

FROM monthly_orders m

JOIN monthly_products p
    ON m.sales_month = p.sales_month

ORDER BY m.sales_month;
"""

result = conn.execute(query).df()

print("\nMONTHLY E-COMMERCE SALES ANALYSIS")
print("=" * 80)
print(result.to_string(index=False))

# Identify highest revenue month
best_month = result.loc[result["order_value_inr"].idxmax()]

print("\nHIGHEST REVENUE MONTH")
print(best_month.to_string())

# Save results
result.to_csv(
    REPORT_DIR / "monthly_sales_analysis.csv",
    index=False
)

conn.close()

print("\nMonthly analysis saved successfully!")
