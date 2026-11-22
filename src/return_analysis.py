
import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

# Return reasons
return_reason_query = """
SELECT
    return_reason,
    COUNT(*) AS total_returns,
    ROUND(SUM(refund_amount), 2) AS total_refund_amount,
    SUM(CASE WHEN return_status = 'Refund Completed'
        THEN 1 ELSE 0 END) AS completed_refunds,
    SUM(CASE WHEN return_status = 'Pending'
        THEN 1 ELSE 0 END) AS pending_returns
FROM returns
GROUP BY return_reason
ORDER BY total_returns DESC
"""

return_reasons = con.execute(return_reason_query).df()

return_reasons.to_csv(
    REPORT_DIR / "return_reason_analysis.csv",
    index=False
)

# Return status
return_status_query = """
SELECT
    return_status,
    COUNT(*) AS total_returns,
    ROUND(SUM(refund_amount), 2) AS total_refund_amount
FROM returns
GROUP BY return_status
ORDER BY total_returns DESC
"""

return_status = con.execute(return_status_query).df()

return_status.to_csv(
    REPORT_DIR / "return_status_analysis.csv",
    index=False
)

# Category-wise returns
category_query = """
SELECT
    p.category,
    COUNT(*) AS total_returns,
    ROUND(SUM(r.refund_amount), 2) AS total_refund_amount
FROM returns r
JOIN products p
    ON r.product_id = p.product_id
GROUP BY p.category
ORDER BY total_returns DESC
"""

category_returns = con.execute(category_query).df()

category_returns.to_csv(
    REPORT_DIR / "category_return_analysis.csv",
    index=False
)

print("\n========== RETURN REASON ANALYSIS ==========")
print(return_reasons.to_string(index=False))

print("\n========== RETURN STATUS ANALYSIS ==========")
print(return_status.to_string(index=False))

print("\n========== CATEGORY RETURN ANALYSIS ==========")
print(category_returns.to_string(index=False))

con.close()

print("\nReturn analysis completed successfully!")
