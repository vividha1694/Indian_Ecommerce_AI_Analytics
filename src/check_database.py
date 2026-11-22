from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

print("\nDATABASE TABLES:")

print(conn.execute("SHOW TABLES").df())

print("\nCUSTOMERS TABLE:")
print(conn.execute("SELECT * FROM customers LIMIT 5").df())

print("\nORDERS TABLE:")
print(conn.execute("SELECT * FROM orders LIMIT 5").df())

conn.close()