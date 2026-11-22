
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

# Load CSV files
tables = {}

for file in DATA_DIR.glob("*.csv"):
    if file.stem not in ["data_dictionary", "dataset_validation_report"]:
        tables[file.stem] = pd.read_csv(file, dtype=str)

print("\nINDIAN E-COMMERCE RELATIONSHIP VALIDATION")
print("=" * 60)

report = []

def log(message):
    print(message)
    report.append(str(message))

# Check primary key duplicates
primary_keys = {
    "customers": "customer_id",
    "orders": "order_id",
    "products": "product_id",
    "order_items": "order_item_id",
    "payments": "payment_id",
    "shipments": "shipment_id",
    "returns": "return_id",
    "customer_reviews": "review_id",
    "marketing_campaigns": "campaign_id"
}

log("\n1. PRIMARY KEY CHECKS")

for table, column in primary_keys.items():
    df = tables[table]
    duplicate_count = df[column].duplicated().sum()

    log(
        f"{table}.{column}: "
        f"{duplicate_count} duplicate keys"
    )

# Check foreign key relationships
relationships = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("shipments", "order_id", "orders", "order_id"),
    ("returns", "order_id", "orders", "order_id"),
    ("returns", "customer_id", "customers", "customer_id"),
    ("returns", "product_id", "products", "product_id"),
    ("customer_reviews", "order_id", "orders", "order_id"),
    ("customer_reviews", "customer_id", "customers", "customer_id"),
    ("customer_reviews", "product_id", "products", "product_id"),
    ("orders", "campaign_id", "marketing_campaigns", "campaign_id")
]

log("\n2. FOREIGN KEY RELATIONSHIP CHECKS")

for child_table, child_col, parent_table, parent_col in relationships:

    child_values = tables[child_table][child_col].dropna()
    parent_values = tables[parent_table][parent_col].dropna()

    unmatched = child_values[~child_values.isin(parent_values)]

    log(
        f"\n{child_table}.{child_col} -> "
        f"{parent_table}.{parent_col}"
    )

    log(f"Non-missing values: {len(child_values)}")
    log(f"Unmatched values: {len(unmatched)}")
    log(f"Missing values: {tables[child_table][child_col].isna().sum()}")

    if len(unmatched) > 0:
        log(f"Example unmatched IDs: {unmatched.head(5).tolist()}")

# Save report
report_path = REPORT_DIR / "relationship_validation.txt"

report_path.write_text(
    "\n".join(report),
    encoding="utf-8"
)

print("\n" + "=" * 60)
print(f"Report saved: {report_path}")
print("=" * 60)
