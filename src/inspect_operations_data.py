
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

tables = ["payments", "returns", "shipments"]

for table in tables:
    print(f"\n{'=' * 55}")
    print(f"TABLE: {table.upper()}")
    print("=" * 55)

    # Display column names and data types
    schema = con.execute(
        f"DESCRIBE SELECT * FROM {table}"
    ).df()

    print("\nColumns:")
    print(schema[["column_name", "column_type"]].to_string(index=False))

    # Display first 5 records
    print("\nSample records:")
    sample = con.execute(
        f"SELECT * FROM {table} LIMIT 5"
    ).df()

    print(sample.to_string(index=False))

con.close()
