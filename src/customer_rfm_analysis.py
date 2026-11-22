
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

conn = duckdb.connect(str(DB_PATH), read_only=True)

query = """
WITH customer_metrics AS (

    SELECT
        customer_id,

        MAX(CAST(order_date AS DATE)) AS last_purchase_date,

        COUNT(DISTINCT order_id) AS frequency,

        SUM(final_amount) AS monetary

    FROM orders

    WHERE order_status = 'Delivered'

    GROUP BY customer_id
),

reference_date AS (

    SELECT
        MAX(CAST(order_date AS DATE)) + INTERVAL 1 DAY
        AS analysis_date

    FROM orders
),

rfm AS (

    SELECT
        c.customer_id,
        c.last_purchase_date,

        DATE_DIFF(
            'day',
            c.last_purchase_date,
            r.analysis_date
        ) AS recency_days,

        c.frequency,
        c.monetary

    FROM customer_metrics c
    CROSS JOIN reference_date r
),

rfm_scores AS (

    SELECT
        *,

        NTILE(5) OVER (
            ORDER BY recency_days DESC
        ) AS recency_score,

        NTILE(5) OVER (
            ORDER BY frequency ASC
        ) AS frequency_score,

        NTILE(5) OVER (
            ORDER BY monetary ASC
        ) AS monetary_score

    FROM rfm
),

customer_segments AS (

    SELECT
        *,

        recency_score +
        frequency_score +
        monetary_score AS rfm_total_score,

        CASE

            WHEN recency_score >= 4
             AND frequency_score >= 4
             AND monetary_score >= 4
                THEN 'Champions'

            WHEN frequency_score >= 4
             AND monetary_score >= 3
                THEN 'Loyal Customers'

            WHEN recency_score <= 2
             AND frequency_score >= 3
                THEN 'At Risk'

            WHEN frequency_score = 1
             AND recency_score >= 4
                THEN 'New Customers'

            WHEN recency_score >= 4
             AND frequency_score >= 2
                THEN 'Potential Loyalists'

            ELSE 'Regular Customers'

        END AS customer_segment

    FROM rfm_scores
)

SELECT *
FROM customer_segments
ORDER BY rfm_total_score DESC, monetary DESC;
"""

result = conn.execute(query).df()

print("\nCUSTOMER RFM ANALYSIS")
print("=" * 85)
print(result.head(15).to_string(index=False))

# Customer segment summary
segment_query = """
WITH customer_metrics AS (
    SELECT
        customer_id,
        MAX(CAST(order_date AS DATE)) AS last_purchase_date,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(final_amount) AS monetary
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
),

reference_date AS (
    SELECT
        MAX(CAST(order_date AS DATE)) + INTERVAL 1 DAY
        AS analysis_date
    FROM orders
),

rfm AS (
    SELECT
        c.*,
        DATE_DIFF('day', c.last_purchase_date, r.analysis_date)
            AS recency_days
    FROM customer_metrics c
    CROSS JOIN reference_date r
),

scores AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m
    FROM rfm
),

segments AS (
    SELECT
        CASE
            WHEN r >= 4 AND f >= 4 AND m >= 4
                THEN 'Champions'
            WHEN f >= 4 AND m >= 3
                THEN 'Loyal Customers'
            WHEN r <= 2 AND f >= 3
                THEN 'At Risk'
            WHEN f = 1 AND r >= 4
                THEN 'New Customers'
            WHEN r >= 4 AND f >= 2
                THEN 'Potential Loyalists'
            ELSE 'Regular Customers'
        END AS customer_segment,

        frequency,
        monetary

    FROM scores
)

SELECT
    customer_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(frequency), 2) AS average_orders,
    ROUND(AVG(monetary), 2) AS average_spend_inr,
    ROUND(SUM(monetary), 2) AS total_spend_inr

FROM segments

GROUP BY customer_segment

ORDER BY customer_count DESC;
"""

summary = conn.execute(segment_query).df()

print("\nCUSTOMER SEGMENT SUMMARY")
print("=" * 85)
print(summary.to_string(index=False))

# Repeat customer analysis
repeat_query = """
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
)

SELECT
    COUNT(*) AS purchasing_customers,

    COUNT(*) FILTER (
        WHERE order_count >= 2
    ) AS repeat_customers,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_count >= 2
        ) / COUNT(*),
        2
    ) AS repeat_customer_rate_percent

FROM customer_orders;
"""

repeat_result = conn.execute(repeat_query).df()

print("\nREPEAT CUSTOMER ANALYSIS")
print("=" * 85)
print(repeat_result.to_string(index=False))

# Save reports
result.to_csv(
    REPORT_DIR / "customer_rfm_details.csv",
    index=False
)

summary.to_csv(
    REPORT_DIR / "customer_segment_summary.csv",
    index=False
)

repeat_result.to_csv(
    REPORT_DIR / "repeat_customer_analysis.csv",
    index=False
)

conn.close()

print("\nCustomer RFM analysis completed successfully!")
print("Three reports saved in the reports folder.")
