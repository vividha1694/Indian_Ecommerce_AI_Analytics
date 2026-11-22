
from pathlib import Path
import duckdb

# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "cleaned"
DB_DIR = BASE_DIR / "database"

DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "ecommerce_analytics.duckdb"

# Connect to DuckDB
conn = duckdb.connect(str(DB_PATH))

# Business tables to load
table_names = [
    "customers",
    "orders",
    "order_items",
    "products",
    "payments",
    "returns",
    "shipments",
    "customer_reviews",
    "marketing_campaigns"
]

print("=" * 60)
print("CREATING INDIAN E-COMMERCE ANALYTICS DATABASE")
print("=" * 60)

for table in table_names:

    csv_path = DATA_DIR / f"{table}.csv"

    if not csv_path.exists():
        print(f"FILE NOT FOUND: {csv_path}")
        continue

    # Load CSV into DuckDB table
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT *
        FROM read_csv_auto(?, header = true)
        """,
        [str(csv_path)]
    )

    row_count = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {row_count:,} records loaded")

# Show database tables
print("\nDATABASE TABLES:")

tables = conn.execute(
    "SHOW TABLES"
).fetchall()

for table in tables:
    print("-", table[0])

conn.close()

print("\n" + "=" * 60)
print("DATABASE CREATED SUCCESSFULLY!")
print(f"Location: {DB_PATH}")
print("=" * 60)
