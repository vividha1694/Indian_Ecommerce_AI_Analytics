
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

conn = duckdb.connect(str(DB_PATH), read_only=True)

query = """
WITH state_orders AS (
    SELECT
        delivery_state,
        COUNT(*) AS total_orders,
        SUM(final_amount) AS order_value,
        AVG(final_amount) AS average_order_value

    FROM orders

    WHERE order_status = 'Delivered'

    GROUP BY delivery_state
),

state_products AS (
    SELECT
        o.delivery_state,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.profit) AS product_profit

    FROM orders o

    JOIN order_items oi
        ON o.order_id = oi.order_id

    WHERE o.order_status = 'Delivered'

    GROUP BY o.delivery_state
)

SELECT
    o.delivery_state,
    o.total_orders,

    ROUND(o.order_value, 2) AS order_value_inr,

    ROUND(o.average_order_value, 2)
        AS average_order_value_inr,

    ROUND(p.product_revenue, 2)
        AS product_revenue_inr,

    ROUND(p.product_profit, 2)
        AS product_profit_inr,

    ROUND(
        100.0 * p.product_profit /
        NULLIF(p.product_revenue, 0),
        2
    ) AS profit_margin_percent

FROM state_orders o

JOIN state_products p
    ON o.delivery_state = p.delivery_state

ORDER BY order_value_inr DESC;
"""

result = conn.execute(query).df()

print("\nINDIAN E-COMMERCE STATE-WISE SALES ANALYSIS")
print("=" * 100)
print(result.to_string(index=False))

print("\nTOP 5 STATES BY ORDER VALUE")
print(result.head(5).to_string(index=False))

print("\nLOWEST 5 STATES BY ORDER VALUE")
print(result.tail(5).to_string(index=False))

# Save report
result.to_csv(
    REPORT_DIR / "state_sales_analysis.csv",
    index=False
)

conn.close()

print("\nState-wise analysis saved successfully!")
