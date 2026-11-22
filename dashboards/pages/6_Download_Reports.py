
import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Download Reports",
    page_icon="📥",
    layout="wide"
)

# ==========================================
# 2. PREMIUM LIGHT THEME
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg, #F8F5EF 0%, #F2EEF8 50%, #F8F0EA 100%
    );
    color: #393344;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}
h1, h2, h3 {
    color: #453B50;
    font-family: 'Trebuchet MS', sans-serif;
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.78);
    border: 1px solid #E8DDEA;
    border-radius: 18px;
    padding: 20px 16px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "ecommerce_analytics.duckdb"

@st.cache_resource
def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

con = get_connection()

# ==========================================
# 4. HEADER
# ==========================================

st.markdown("""
<div style="
    background: linear-gradient(110deg, #E8DDF7, #F9DFD2);
    padding: 30px;
    border-radius: 22px;
    margin-bottom: 20px;
">
    <div style="
        color: #725F80;
        font-size: 13px;
        letter-spacing: 2px;
        font-weight: 700;
    ">
        BUSINESS INTELLIGENCE PLATFORM
    </div>
    <h1 style="color:#45364F; margin-bottom:8px;">
        Download Business Reports
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Export sales, customer, product and operational
        performance into a single Excel workbook.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Reports are generated from the synthetic Indian ecommerce dataset. "
    "They do not represent actual company transactions."
)

# ==========================================
# 5. DATE FILTER
# ==========================================

min_date, max_date = con.execute("""
    SELECT MIN(order_date), MAX(order_date)
    FROM orders
""").fetchone()

min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

date_range = st.sidebar.date_input(
    "Select Report Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

if len(date_range) != 2:
    st.info("Please select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range

if start_date > end_date:
    st.error("Start date cannot be after end date.")
    st.stop()

params = [start_date, end_date]

st.sidebar.divider()
st.sidebar.markdown("### Selected Period")
st.sidebar.write(f"From: {start_date.strftime('%d %b %Y')}")
st.sidebar.write(f"To: {end_date.strftime('%d %b %Y')}")

# ==========================================
# 6. EXECUTIVE SUMMARY
# ==========================================

sales_kpi = con.execute("""
    SELECT
        COUNT(*) AS delivered_orders,
        COALESCE(SUM(final_amount), 0) AS order_value,
        AVG(final_amount) AS average_order_value,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_date BETWEEN ? AND ?
""", params).df().iloc[0]

product_kpi = con.execute("""
    SELECT
        COALESCE(SUM(oi.item_revenue), 0) AS product_revenue,
        COALESCE(SUM(oi.item_cost), 0) AS product_cost,
        COALESCE(
            SUM(oi.item_revenue - oi.item_cost), 0
        ) AS product_profit
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

product_revenue = product_kpi["product_revenue"]
product_profit = product_kpi["product_profit"]

profit_margin = (
    product_profit / product_revenue * 100
    if product_revenue else 0
)

summary = pd.DataFrame({
    "Metric": [
        "Report Start Date",
        "Report End Date",
        "Delivered Orders",
        "Delivered Order Value (INR)",
        "Average Order Value (INR)",
        "Unique Customers",
        "Product Revenue (INR)",
        "Product Cost (INR)",
        "Product Profit (INR)",
        "Product Profit Margin (%)"
    ],
    "Value": [
        str(start_date),
        str(end_date),
        int(sales_kpi["delivered_orders"]),
        round(sales_kpi["order_value"], 2),
        round(sales_kpi["average_order_value"], 2)
        if pd.notna(sales_kpi["average_order_value"]) else 0,
        int(sales_kpi["unique_customers"]),
        round(product_revenue, 2),
        round(product_kpi["product_cost"], 2),
        round(product_profit, 2),
        round(profit_margin, 2)
    ]
})

# ==========================================
# 7. MONTHLY SALES REPORT
# ==========================================

monthly_sales = con.execute("""
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        COUNT(*) AS delivered_orders,
        COUNT(DISTINCT customer_id) AS unique_customers,
        SUM(final_amount) AS order_value
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_date BETWEEN ? AND ?
    GROUP BY month
    ORDER BY month
""", params).df()

# ==========================================
# 8. CATEGORY PERFORMANCE REPORT
# ==========================================

category_report = con.execute("""
    SELECT
        p.category,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.item_cost) AS product_cost,
        SUM(oi.item_revenue - oi.item_cost) AS product_profit,
        SUM(oi.quantity) AS units_sold,
        COUNT(DISTINCT oi.product_id) AS products_sold
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY p.category
    ORDER BY product_revenue DESC
""", params).df()

category_report["profit_margin_percent"] = (
    category_report["product_profit"] /
    category_report["product_revenue"].replace(0, pd.NA) * 100
).fillna(0)

# ==========================================
# 9. STATE PERFORMANCE REPORT
# ==========================================

state_report = con.execute("""
    SELECT
        c.state,
        COUNT(o.order_id) AS delivered_orders,
        COUNT(DISTINCT o.customer_id) AS unique_customers,
        SUM(o.final_amount) AS order_value
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY c.state
    ORDER BY order_value DESC
""", params).df()

# ==========================================
# 10. CUSTOMER PERFORMANCE REPORT
# ==========================================

customer_report = con.execute("""
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS delivered_orders,
        SUM(o.final_amount) AS customer_value,
        AVG(o.final_amount) AS average_order_value,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS last_order_date
    FROM orders o
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY o.customer_id
    ORDER BY customer_value DESC
""", params).df()

# ==========================================
# 11. PAYMENT METHOD REPORT
# ==========================================

payment_report = con.execute("""
    SELECT
        p.payment_method,
        COUNT(*) AS total_transactions,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Success'
        ) AS successful_payments,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Failed'
        ) AS failed_payments,

        ROUND(
            COUNT(*) FILTER (
                WHERE p.payment_status = 'Success'
            ) * 100.0 /
            NULLIF(
                COUNT(*) FILTER (
                    WHERE p.payment_status IN ('Success', 'Failed')
                ), 0
            ), 2
        ) AS success_rate_percent,

        SUM(p.amount_paid) FILTER (
            WHERE p.payment_status = 'Success'
        ) AS successful_amount

    FROM payments p
    JOIN orders o
        ON p.order_id = o.order_id
    WHERE o.order_date BETWEEN ? AND ?
    GROUP BY p.payment_method
    ORDER BY successful_payments DESC
""", params).df()

# ==========================================
# 12. RETURN REASONS REPORT
# ==========================================

return_report = con.execute("""
    SELECT
        r.return_reason,
        COUNT(*) AS total_return_records,
        SUM(r.refund_amount) AS refund_amount
    FROM returns r
    JOIN orders o
        ON r.order_id = o.order_id
    WHERE o.order_date BETWEEN ? AND ?
    GROUP BY r.return_reason
    ORDER BY total_return_records DESC
""", params).df()

# ==========================================
# 13. DELIVERY PERFORMANCE REPORT
# ==========================================

delivery_report = con.execute("""
    SELECT
        s.shipping_method,
        COUNT(*) AS delivered_shipments,

        COUNT(*) FILTER (
            WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
        ) AS delayed_shipments,

        ROUND(AVG(s.delivery_days), 2) AS average_delivery_days,

        ROUND(
            COUNT(*) FILTER (
                WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
            ) * 100.0 / NULLIF(COUNT(*), 0), 2
        ) AS delay_rate_percent

    FROM shipments s
    JOIN orders o
        ON s.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY s.shipping_method
    ORDER BY delayed_shipments DESC
""", params).df()

# ==========================================
# 14. REPORT DEFINITIONS
# ==========================================

definitions = pd.DataFrame({
    "Report Term": [
        "Delivered Orders",
        "Delivered Order Value",
        "Product Revenue",
        "Product Cost",
        "Product Profit",
        "Product Profit Margin",
        "Average Order Value",
        "Unique Customers",
        "Payment Success Rate",
        "Delivery Delay Rate"
    ],
    "Definition": [
        "Orders with order_status equal to Delivered.",
        "Sum of final_amount for delivered orders; includes shipping and tax.",
        "Sum of item_revenue for delivered order items.",
        "Sum of item_cost for delivered order items.",
        "Product revenue minus product cost.",
        "Product profit divided by product revenue, multiplied by 100.",
        "Delivered order value divided by delivered order count.",
        "Distinct customers with delivered orders in the selected period.",
        "Successful payment transactions divided by successful plus failed transactions.",
        "Delayed delivered shipments divided by delivered shipments."
    ]
})

# ==========================================
# 15. DISPLAY REPORT PREVIEW
# ==========================================

st.subheader("Report Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Delivered Orders",
    f"{int(sales_kpi['delivered_orders']):,}"
)

c2.metric(
    "Order Value",
    f"₹{sales_kpi['order_value'] / 10000000:.2f} Cr"
)

c3.metric(
    "Unique Customers",
    f"{int(sales_kpi['unique_customers']):,}"
)

c4.metric(
    "Product Profit",
    f"₹{product_profit / 10000000:.2f} Cr"
)

st.divider()

st.subheader("Reports Included")

report_descriptions = [
    ("Executive Summary", "Key business KPIs and financial metrics."),
    ("Monthly Sales", "Monthly delivered orders, customers and order value."),
    ("Category Performance", "Revenue, cost, profit, units and margin by category."),
    ("State Performance", "Delivered orders, customers and order value by state."),
    ("Customer Performance", "Customer purchase frequency and order value."),
    ("Payment Methods", "Transaction counts, success rates and successful amounts."),
    ("Return Reasons", "Return counts and refund amounts by reason."),
    ("Delivery Performance", "Delayed shipments and average delivery time by shipping method."),
    ("Definitions", "Explanation of the business metrics used in this workbook.")
]

for title, description in report_descriptions:
    st.markdown(f"**{title}** — {description}")

st.divider()

# ==========================================
# 16. CREATE EXCEL WORKBOOK
# ==========================================

def create_excel_report():

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        summary.to_excel(
            writer,
            sheet_name="Executive Summary",
            index=False
        )

        monthly_sales.to_excel(
            writer,
            sheet_name="Monthly Sales",
            index=False
        )

        category_report.to_excel(
            writer,
            sheet_name="Category Performance",
            index=False
        )

        state_report.to_excel(
            writer,
            sheet_name="State Performance",
            index=False
        )

        customer_report.to_excel(
            writer,
            sheet_name="Customer Performance",
            index=False
        )

        payment_report.to_excel(
            writer,
            sheet_name="Payment Methods",
            index=False
        )

        return_report.to_excel(
            writer,
            sheet_name="Return Reasons",
            index=False
        )

        delivery_report.to_excel(
            writer,
            sheet_name="Delivery Performance",
            index=False
        )

        definitions.to_excel(
            writer,
            sheet_name="Definitions",
            index=False
        )

    output.seek(0)

    # ======================================
    # 17. EXCEL FORMATTING
    # ======================================

    workbook = load_workbook(output)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="59476C"
    )

    for worksheet in workbook.worksheets:

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = Font(
                bold=True,
                color="FFFFFF",
                size=11
            )
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

        for column_cells in worksheet.columns:

            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                if cell.value is not None:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )

            worksheet.column_dimensions[
                column_letter
            ].width = min(max_length + 4, 38)

        worksheet.sheet_view.showGridLines = False

    final_output = BytesIO()

    workbook.save(final_output)

    final_output.seek(0)

    return final_output.getvalue()

# ==========================================
# 18. DOWNLOAD BUTTON
# ==========================================

st.subheader("Download Your Business Report")

st.write(
    "Generate one Excel workbook containing all nine reports. "
    "The selected date range is applied to the business data."
)

if st.button("Generate Excel Report", width="stretch"):

    with st.spinner("Preparing your Excel workbook..."):

        excel_data = create_excel_report()

        st.session_state["excel_report"] = excel_data

    st.success("Your Excel report has been generated successfully!")

if "excel_report" in st.session_state:

    filename = (
        f"Ecommerce_Business_Report_"
        f"{start_date}_{end_date}.xlsx"
    )

    st.download_button(
        label="Download Excel Workbook",
        data=st.session_state["excel_report"],
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch"
    )

st.divider()

# ==========================================
# 19. CSV DOWNLOADS
# ==========================================

st.subheader("Download Individual CSV Reports")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "Download Monthly Sales CSV",
        data=monthly_sales.to_csv(index=False).encode("utf-8"),
        file_name="monthly_sales_report.csv",
        mime="text/csv",
        width="stretch"
    )

with col2:
    st.download_button(
        "Download Category Performance CSV",
        data=category_report.to_csv(index=False).encode("utf-8"),
        file_name="category_performance_report.csv",
        mime="text/csv",
        width="stretch"
    )

st.caption(
    "The Excel workbook contains nine worksheets. "
    "Financial metrics are calculated using the definitions "
    "provided in the Definitions worksheet."
)
