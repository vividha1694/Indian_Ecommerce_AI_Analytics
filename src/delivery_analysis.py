
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

# Shipping method performance
shipping_query = """
SELECT
    shipping_method,
    COUNT(*) AS total_shipments,

    SUM(CASE WHEN delivery_status = 'Delivered'
        THEN 1 ELSE 0 END) AS delivered_shipments,

    SUM(CASE WHEN delayed_flag = 1
        THEN 1 ELSE 0 END) AS delayed_shipments,

    ROUND(AVG(delivery_days), 2) AS average_delivery_days,

    ROUND(
        100.0 * SUM(CASE WHEN delayed_flag = 1
            THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS delay_rate_percent

FROM shipments
GROUP BY shipping_method
ORDER BY total_shipments DESC
"""

shipping = con.execute(shipping_query).df()

shipping.to_csv(
    REPORT_DIR / "shipping_method_analysis.csv",
    index=False
)

# Warehouse performance
warehouse_query = """
SELECT
    warehouse_city,
    COUNT(*) AS total_shipments,

    SUM(CASE WHEN delivery_status = 'Delivered'
        THEN 1 ELSE 0 END) AS delivered_shipments,

    SUM(CASE WHEN delayed_flag = 1
        THEN 1 ELSE 0 END) AS delayed_shipments,

    ROUND(AVG(delivery_days), 2) AS average_delivery_days,

    ROUND(
        100.0 * SUM(CASE WHEN delayed_flag = 1
            THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS delay_rate_percent

FROM shipments
GROUP BY warehouse_city
ORDER BY total_shipments DESC
"""

warehouse = con.execute(warehouse_query).df()

warehouse.to_csv(
    REPORT_DIR / "warehouse_delivery_analysis.csv",
    index=False
)

# Overall delivery performance
overall_query = """
SELECT
    COUNT(*) AS total_shipments,

    SUM(CASE WHEN delivery_status = 'Delivered'
        THEN 1 ELSE 0 END) AS delivered_shipments,

    SUM(CASE WHEN delayed_flag = 1
        THEN 1 ELSE 0 END) AS delayed_shipments,

    ROUND(AVG(delivery_days), 2) AS average_delivery_days,

    ROUND(
        100.0 * SUM(CASE WHEN delayed_flag = 1
            THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS overall_delay_rate_percent

FROM shipments
"""

overall = con.execute(overall_query).df()

overall.to_csv(
    REPORT_DIR / "overall_delivery_analysis.csv",
    index=False
)

print("\n========== SHIPPING METHOD ANALYSIS ==========")
print(shipping.to_string(index=False))

print("\n========== WAREHOUSE DELIVERY ANALYSIS ==========")
print(warehouse.to_string(index=False))

print("\n========== OVERALL DELIVERY PERFORMANCE ==========")
print(overall.to_string(index=False))

con.close()

print("\nDelivery analysis completed successfully!")
