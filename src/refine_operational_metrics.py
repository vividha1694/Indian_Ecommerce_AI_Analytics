
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Payment success rate among successful and failed attempts
payment_query = """
SELECT
    payment_method,
    COUNT(*) AS total_transactions,

    SUM(CASE WHEN payment_status = 'Success'
        THEN 1 ELSE 0 END) AS successful_transactions,

    SUM(CASE WHEN payment_status = 'Failed'
        THEN 1 ELSE 0 END) AS failed_transactions,

    SUM(CASE WHEN payment_status = 'Refunded'
        THEN 1 ELSE 0 END) AS refunded_transactions,

    SUM(CASE WHEN payment_status = 'Pending'
        THEN 1 ELSE 0 END) AS pending_transactions,

    SUM(CASE WHEN payment_status = 'Not Charged'
        THEN 1 ELSE 0 END) AS not_charged_transactions,

    ROUND(
        100.0 * SUM(CASE WHEN payment_status = 'Success'
            THEN 1 ELSE 0 END)
        / NULLIF(
            SUM(CASE WHEN payment_status IN ('Success', 'Failed')
                THEN 1 ELSE 0 END), 0
        ), 2
    ) AS attempt_success_rate_percent

FROM payments
GROUP BY payment_method
ORDER BY total_transactions DESC
"""

payment = con.execute(payment_query).df()
payment.to_csv(
    REPORT_DIR / "refined_payment_analysis.csv",
    index=False
)

# 2. Return analysis with completed and approved refunds separated
return_query = """
SELECT
    return_status,
    COUNT(*) AS total_return_records,

    SUM(CASE WHEN return_status = 'Refund Completed'
        THEN 1 ELSE 0 END) AS completed_refunds,

    SUM(CASE WHEN return_status = 'Approved'
        THEN 1 ELSE 0 END) AS approved_returns,

    SUM(CASE WHEN return_status = 'Pending'
        THEN 1 ELSE 0 END) AS pending_returns,

    SUM(CASE WHEN return_status = 'Rejected'
        THEN 1 ELSE 0 END) AS rejected_returns,

    ROUND(SUM(CASE WHEN return_status = 'Refund Completed'
        THEN refund_amount ELSE 0 END), 2)
        AS completed_refund_amount,

    ROUND(SUM(CASE WHEN return_status = 'Approved'
        THEN refund_amount ELSE 0 END), 2)
        AS approved_refund_amount

FROM returns
GROUP BY return_status
ORDER BY total_return_records DESC
"""

returns = con.execute(return_query).df()
returns.to_csv(
    REPORT_DIR / "refined_return_status_analysis.csv",
    index=False
)

# 3. Category-wise return rate based on eligible product lines
category_query = """
WITH eligible_items AS (
    SELECT DISTINCT
        oi.order_id,
        oi.product_id,
        p.category
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status IN ('Delivered', 'Returned')
),

category_totals AS (
    SELECT
        category,
        COUNT(*) AS eligible_product_lines
    FROM eligible_items
    GROUP BY category
),

category_returns AS (
    SELECT
        p.category,
        COUNT(DISTINCT (r.order_id, r.product_id))
            AS returned_product_lines
    FROM returns r
    JOIN products p
        ON r.product_id = p.product_id
    GROUP BY p.category
)

SELECT
    t.category,
    t.eligible_product_lines,
    COALESCE(r.returned_product_lines, 0)
        AS returned_product_lines,

    ROUND(
        100.0 * COALESCE(r.returned_product_lines, 0)
        / NULLIF(t.eligible_product_lines, 0), 2
    ) AS product_line_return_rate_percent

FROM category_totals t
LEFT JOIN category_returns r
    ON t.category = r.category
ORDER BY product_line_return_rate_percent DESC
"""

category_returns = con.execute(category_query).df()
category_returns.to_csv(
    REPORT_DIR / "refined_category_return_rate.csv",
    index=False
)

# 4. Delivery performance: delivered shipments only
delivery_query = """
SELECT
    shipping_method,
    COUNT(*) AS delivered_shipments,

    SUM(CASE WHEN delayed_flag = 1
        THEN 1 ELSE 0 END) AS delayed_delivered_shipments,

    ROUND(AVG(delivery_days), 2)
        AS average_delivery_days,

    ROUND(
        100.0 * SUM(CASE WHEN delayed_flag = 1
            THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS delivered_shipment_delay_rate_percent

FROM shipments
WHERE delivery_status = 'Delivered'
GROUP BY shipping_method
ORDER BY delivered_shipment_delay_rate_percent DESC
"""

delivery = con.execute(delivery_query).df()
delivery.to_csv(
    REPORT_DIR / "refined_delivery_analysis.csv",
    index=False
)

# 5. Overall shipment status
status_query = """
SELECT
    delivery_status,
    COUNT(*) AS total_shipments
FROM shipments
GROUP BY delivery_status
ORDER BY total_shipments DESC
"""

shipment_status = con.execute(status_query).df()
shipment_status.to_csv(
    REPORT_DIR / "shipment_status_analysis.csv",
    index=False
)

# 6. Warehouse performance: delivered shipments only
warehouse_query = """
SELECT
    warehouse_city,
    COUNT(*) AS delivered_shipments,

    SUM(CASE WHEN delayed_flag = 1
        THEN 1 ELSE 0 END) AS delayed_delivered_shipments,

    ROUND(AVG(delivery_days), 2)
        AS average_delivery_days,

    ROUND(
        100.0 * SUM(CASE WHEN delayed_flag = 1
            THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS delivered_shipment_delay_rate_percent

FROM shipments
WHERE delivery_status = 'Delivered'
GROUP BY warehouse_city
ORDER BY delivered_shipment_delay_rate_percent DESC
"""

warehouse = con.execute(warehouse_query).df()
warehouse.to_csv(
    REPORT_DIR / "refined_warehouse_analysis.csv",
    index=False
)

print("\n========== REFINED PAYMENT ANALYSIS ==========")
print(payment.to_string(index=False))

print("\n========== RETURN STATUS ANALYSIS ==========")
print(returns.to_string(index=False))

print("\n========== CATEGORY RETURN RATE ==========")
print(category_returns.to_string(index=False))

print("\n========== DELIVERED SHIPMENT PERFORMANCE ==========")
print(delivery.to_string(index=False))

print("\n========== SHIPMENT STATUS ==========")
print(shipment_status.to_string(index=False))

print("\n========== WAREHOUSE PERFORMANCE ==========")
print(warehouse.to_string(index=False))

con.close()

print("\nRefined operational analysis completed!")
