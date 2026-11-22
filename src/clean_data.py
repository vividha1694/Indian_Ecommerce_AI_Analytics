
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
REPORT_DIR = BASE_DIR / "reports"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Date columns in each business table
date_columns = {
    "customers": ["customer_signup_date", "last_order_date"],
    "orders": ["order_date"],
    "payments": ["payment_date"],
    "products": ["product_launch_date"],
    "returns": ["return_date"],
    "shipments": [
        "dispatch_date",
        "expected_delivery_date",
        "actual_delivery_date"
    ],
    "customer_reviews": ["review_date"],
    "marketing_campaigns": [
        "campaign_start_date",
        "campaign_end_date"
    ]
}

# Values worth investigating, not automatically deleting
numeric_checks = {
    "customers": {
        "age": ("outside_range", 0, 120)
    },
    "orders": {
        "discount_percentage": ("outside_range", 0, 100),
        "subtotal": ("negative",),
        "shipping_fee": ("negative",),
        "tax_amount": ("negative",),
        "final_amount": ("negative",)
    },
    "order_items": {
        "quantity": ("non_positive",),
        "unit_price": ("negative",),
        "discount_percentage": ("outside_range", 0, 100),
        "item_revenue": ("negative",),
        "item_cost": ("negative",)
    },
    "products": {
        "price": ("negative",),
        "cost_price": ("negative",),
        "rating_average": ("outside_range", 1, 5),
        "stock_quantity": ("negative",)
    },
    "customer_reviews": {
        "rating": ("outside_range", 1, 5)
    },
    "marketing_campaigns": {
        "discount_percentage": ("outside_range", 0, 100),
        "campaign_cost": ("negative",),
        "revenue_generated": ("negative",)
    },
    "payments": {
        "amount_paid": ("negative",),
        "transaction_fee": ("negative",),
        "refund_amount": ("negative",)
    },
    "returns": {
        "refund_amount": ("negative",)
    },
    "shipments": {
        "delivery_days": ("negative",)
    }
}

report = []

def log(message=""):
    print(message)
    report.append(str(message))


log("=" * 65)
log("INDIAN E-COMMERCE DATA CLEANING")
log("=" * 65)

# Process business CSV files only
for file in sorted(RAW_DIR.glob("*.csv")):

    table_name = file.stem

    if table_name in [
        "data_dictionary",
        "dataset_validation_report"
    ]:
        continue

    log("\n" + "=" * 65)
    log(f"PROCESSING: {table_name}")
    log("=" * 65)

    df = pd.read_csv(file, low_memory=False)

    original_rows = len(df)

    # Clean whitespace in text columns
    text_columns = df.select_dtypes(include=["object"]).columns

    for col in text_columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace("", pd.NA)

    log(f"Original rows: {original_rows}")

    # Convert known date columns
    for col in date_columns.get(table_name, []):

        if col in df.columns:
            original_non_missing = df[col].notna().sum()

            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

            invalid_dates = (
                original_non_missing - df[col].notna().sum()
            )

            log(f"{col} - invalid date values: {invalid_dates}")

    # Check duplicate complete rows
    duplicate_count = df.duplicated().sum()
    log(f"Duplicate complete rows: {duplicate_count}")

    # Check suspicious numeric values
    log("\nNUMERICAL QUALITY CHECKS:")

    for col, rule in numeric_checks.get(table_name, {}).items():

        if col not in df.columns:
            continue

        values = pd.to_numeric(df[col], errors="coerce")

        if rule[0] == "negative":
            issue_count = (values < 0).sum()

        elif rule[0] == "non_positive":
            issue_count = (values <= 0).sum()

        elif rule[0] == "outside_range":
            issue_count = (
                (values < rule[1]) | (values > rule[2])
            ).sum()

        log(f"{col}: {issue_count} suspicious values")

    # Missing values summary
    log("\nMISSING VALUES:")

    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        log("No missing values.")
    else:
        log(missing.to_string())

    # Save cleaned copy; no rows automatically deleted
    output_file = CLEAN_DIR / f"{table_name}.csv"

    df.to_csv(output_file, index=False)

    log(f"\nSaved cleaned file: {output_file}")
    log(f"Final rows: {len(df)}")

# Save cleaning report
report_file = REPORT_DIR / "data_cleaning_report.txt"

report_file.write_text(
    "\n".join(report),
    encoding="utf-8"
)

log("\n" + "=" * 65)
log("DATA CLEANING PROCESS COMPLETED")
log("=" * 65)
log(f"Report saved: {report_file}")
