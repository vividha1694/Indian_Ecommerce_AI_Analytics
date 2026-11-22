
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "cleaned"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

orders = pd.read_csv(DATA_DIR / "orders.csv")
items = pd.read_csv(DATA_DIR / "order_items.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")

report = []

def log(message=""):
    print(message)
    report.append(str(message))

def compare_values(name, actual, expected):
    difference = (actual - expected).abs()
    tolerance = 0.05

    log(f"\n{name}")
    log(f"Records checked: {len(difference)}")
    log(f"Matching within ₹0.05: {(difference <= tolerance).sum()}")
    log(f"Different: {(difference > tolerance).sum()}")
    log(f"Average absolute difference: ₹{difference.mean():.2f}")
    log(f"Maximum absolute difference: ₹{difference.max():.2f}")

    return difference

log("=" * 65)
log("FINANCIAL DATA VALIDATION")
log("=" * 65)

# 1. Order subtotal vs item revenue
item_totals = items.groupby("order_id")["item_revenue"].sum()

order_comparison = orders[
    ["order_id", "subtotal", "shipping_fee", "tax_amount", "final_amount"]
].copy()

order_comparison["item_total"] = (
    order_comparison["order_id"].map(item_totals)
)

valid = order_comparison.dropna(subset=["item_total"])

diff1 = compare_values(
    "1. ORDER SUBTOTAL VS SUM OF ITEM REVENUE",
    valid["subtotal"],
    valid["item_total"]
)

# 2. Final amount calculation
expected_final = (
    orders["subtotal"] +
    orders["shipping_fee"] +
    orders["tax_amount"]
)

diff2 = compare_values(
    "2. FINAL AMOUNT VS SUBTOTAL + SHIPPING + TAX",
    orders["final_amount"],
    expected_final
)

# 3. Item revenue calculation
expected_revenue = (
    items["quantity"] *
    items["unit_price"] *
    (1 - items["discount_percentage"] / 100)
)

diff3 = compare_values(
    "3. ITEM REVENUE VS QUANTITY, PRICE AND DISCOUNT",
    items["item_revenue"],
    expected_revenue
)

# 4. Item profit calculation
expected_profit = items["item_revenue"] - items["item_cost"]

diff4 = compare_values(
    "4. PROFIT VS ITEM REVENUE MINUS ITEM COST",
    items["profit"],
    expected_profit
)

# 5. Successful payment vs final order amount
successful = payments[
    payments["payment_status"].str.lower().eq("success")
].copy()

payment_totals = successful.groupby("order_id")["amount_paid"].sum()

payment_comparison = orders[
    ["order_id", "final_amount"]
].copy()

payment_comparison["amount_paid"] = (
    payment_comparison["order_id"].map(payment_totals)
)

valid_payments = payment_comparison.dropna(
    subset=["amount_paid"]
)

diff5 = compare_values(
    "5. SUCCESSFUL PAYMENT VS ORDER FINAL AMOUNT",
    valid_payments["amount_paid"],
    valid_payments["final_amount"]
)

# Save detailed differences for further investigation
order_comparison["subtotal_difference"] = diff1.reindex(
    order_comparison.index
)

order_comparison["final_amount_difference"] = diff2

order_comparison.to_csv(
    REPORT_DIR / "order_financial_differences.csv",
    index=False
)

log("\n" + "=" * 65)
log("FINANCIAL VALIDATION COMPLETED")
log("Differences saved for investigation.")
log("=" * 65)

(REPORT_DIR / "financial_validation.txt").write_text(
    "\n".join(report),
    encoding="utf-8"
)
