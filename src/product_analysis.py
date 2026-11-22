
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Category performance
category_query = """
SELECT
    p.category,

    COUNT(DISTINCT oi.order_id) AS total_orders,

    SUM(oi.quantity) AS units_sold,

    ROUND(SUM(oi.item_revenue), 2)
        AS product_revenue_inr,

    ROUND(SUM(oi.item_cost), 2)
        AS product_cost_inr,

    ROUND(SUM(oi.profit), 2)
        AS product_profit_inr,

    ROUND(
        100.0 * SUM(oi.profit) /
        NULLIF(SUM(oi.item_revenue), 0),
        2
    ) AS profit_margin_percent

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

WHERE o.order_status = 'Delivered'

GROUP BY p.category

ORDER BY product_revenue_inr DESC;
"""

category_result = conn.execute(category_query).df()

print("\nCATEGORY PERFORMANCE ANALYSIS")
print("=" * 100)
print(category_result.to_string(index=False))

# Top 10 products
product_query = """
SELECT
    p.product_id,
    p.product_name,
    p.category,

    SUM(oi.quantity) AS units_sold,

    COUNT(DISTINCT oi.order_id) AS total_orders,

    ROUND(SUM(oi.item_revenue), 2)
        AS product_revenue_inr,

    ROUND(SUM(oi.profit), 2)
        AS product_profit_inr,

    ROUND(
        100.0 * SUM(oi.profit) /
        NULLIF(SUM(oi.item_revenue), 0),
        2
    ) AS profit_margin_percent

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

WHERE o.order_status = 'Delivered'

GROUP BY
    p.product_id,
    p.product_name,
    p.category

ORDER BY product_revenue_inr DESC

LIMIT 10;
"""

product_result = conn.execute(product_query).df()

print("\nTOP 10 PRODUCTS BY REVENUE")
print("=" * 100)
print(product_result.to_string(index=False))

# Save reports
category_result.to_csv(
    REPORT_DIR / "category_performance.csv",
    index=False
)

product_result.to_csv(
    REPORT_DIR / "top_10_products.csv",
    index=False
)

conn.close()

print("\nProduct analysis completed successfully!")
