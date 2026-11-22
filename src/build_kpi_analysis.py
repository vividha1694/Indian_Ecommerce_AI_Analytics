from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Main business KPI calculation
query = """
WITH order_metrics AS (
    SELECT
        COUNT(*) AS total_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'Delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'Cancelled'
        ) AS cancelled_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'Returned'
        ) AS returned_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'Failed'
        ) AS failed_orders,

        COUNT(*) FILTER (
            WHERE order_status = 'Processing'
        ) AS processing_orders,

        SUM(final_amount) FILTER (
            WHERE order_status = 'Delivered'
        ) AS delivered_order_value,

        AVG(final_amount) FILTER (
            WHERE order_status = 'Delivered'
        ) AS average_delivered_order_value

    FROM orders
),

product_metrics AS (
    SELECT
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.item_cost) AS product_cost,
        SUM(oi.profit) AS product_profit

    FROM order_items oi

    INNER JOIN orders o
        ON oi.order_id = o.order_id

    WHERE o.order_status = 'Delivered'
)

SELECT
    o.total_orders,
    o.delivered_orders,
    o.cancelled_orders,
    o.returned_orders,
    o.failed_orders,
    o.processing_orders,

    ROUND(o.delivered_order_value, 2)
        AS delivered_order_value_inr,

    ROUND(o.average_delivered_order_value, 2)
        AS average_order_value_inr,

    ROUND(p.product_revenue, 2)
        AS delivered_product_revenue_inr,

    ROUND(p.product_cost, 2)
        AS delivered_product_cost_inr,

    ROUND(p.product_profit, 2)
        AS delivered_product_profit_inr,

    ROUND(
        100.0 * p.product_profit /
        NULLIF(p.product_revenue, 0),
        2
    ) AS product_profit_margin_percent,

    ROUND(
        100.0 * o.returned_orders /
        NULLIF(o.delivered_orders + o.returned_orders, 0),
        2
    ) AS order_return_rate_percent

FROM order_metrics o
CROSS JOIN product_metrics p;
"""

result = conn.execute(query).df()

print("\nINDIAN E-COMMERCE BUSINESS KPI REPORT")
print("=" * 70)
print(result.T.to_string(header=False))

# Save KPI report
output_path = REPORT_DIR / "ecommerce_kpi_summary.csv"
result.to_csv(output_path, index=False)

# Order status distribution
status_query = """
SELECT
    order_status,
    COUNT(*) AS total_orders,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;
"""

status_result = conn.execute(status_query).df()

status_result.to_csv(
    REPORT_DIR / "order_status_summary.csv",
    index=False
)

print("\n\nORDER STATUS SUMMARY")
print(status_result.to_string(index=False))

conn.close()

print("\nKPI REPORTS SAVED SUCCESSFULLY!")