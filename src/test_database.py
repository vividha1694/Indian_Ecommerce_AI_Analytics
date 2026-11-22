from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

query = """
SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(final_amount), 2) AS total_order_value,
    ROUND(AVG(final_amount), 2) AS average_order_value
FROM orders;
"""

result = conn.execute(query).df()

print("\nFIRST E-COMMERCE BUSINESS ANALYSIS")
print(result.to_string(index=False))

conn.close()