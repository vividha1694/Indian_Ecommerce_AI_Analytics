
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

# Payment method performance
payment_method_query = """
SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)
        AS successful_transactions,
    SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END)
        AS failed_transactions,
    SUM(CASE WHEN payment_status = 'Not Charged' THEN 1 ELSE 0 END)
        AS not_charged_transactions,
    ROUND(
        100.0 * SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS success_rate_percent,
    ROUND(SUM(amount_paid), 2) AS total_amount_paid,
    ROUND(SUM(transaction_fee), 2) AS total_transaction_fees,
    ROUND(SUM(refund_amount), 2) AS total_refunds
FROM payments
GROUP BY payment_method
ORDER BY total_transactions DESC
"""

payment_method = con.execute(payment_method_query).df()

payment_method.to_csv(
    REPORT_DIR / "payment_method_analysis.csv",
    index=False
)

# Payment status summary
payment_status_query = """
SELECT
    payment_status,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_paid), 2) AS total_amount_paid,
    ROUND(SUM(refund_amount), 2) AS total_refunds
FROM payments
GROUP BY payment_status
ORDER BY total_transactions DESC
"""

payment_status = con.execute(payment_status_query).df()

payment_status.to_csv(
    REPORT_DIR / "payment_status_analysis.csv",
    index=False
)

print("\n========== PAYMENT METHOD ANALYSIS ==========")
print(payment_method.to_string(index=False))

print("\n========== PAYMENT STATUS ANALYSIS ==========")
print(payment_status.to_string(index=False))

con.close()

print("\nPayment analysis completed successfully!")
