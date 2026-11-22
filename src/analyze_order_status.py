
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Analyse order status
query = """
SELECT
    order_status,
    COUNT(*) AS total_orders,
    ROUND(SUM(final_amount), 2) AS total_order_value,
    ROUND(AVG(final_amount), 2) AS average_order_value
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;
"""

result = conn.execute(query).df()

print("\nINDIAN E-COMMERCE ORDER STATUS ANALYSIS")
print("=" * 65)
print(result.to_string(index=False))

# Check overall order date range
date_query = """
SELECT
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
FROM orders;
"""

print("\nORDER DATE RANGE")
print(conn.execute(date_query).df().to_string(index=False))

conn.close()
