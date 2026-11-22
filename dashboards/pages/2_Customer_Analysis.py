
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Customer Analysis",
    page_icon="👥",
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
    box-shadow: 0 5px 18px rgba(89,68,105,0.06);
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
        Customer Analysis
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Understand customer behaviour, repeat purchases,
        customer value and regional distribution.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Customer metrics are based on delivered orders "
    "from a synthetic Indian ecommerce dataset."
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
    "Select Order Date Range",
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
# 6. CUSTOMER-LEVEL DATA
# ==========================================

customer_data = con.execute("""
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(final_amount) AS customer_value,
        MIN(order_date) AS first_order,
        MAX(order_date) AS last_order
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_date BETWEEN ? AND ?
    GROUP BY customer_id
""", params).df()

# ==========================================
# 7. CUSTOMER KPI CALCULATIONS
# ==========================================

total_customers = len(customer_data)

repeat_customers = int(
    (customer_data["order_count"] > 1).sum()
)

one_time_customers = int(
    (customer_data["order_count"] == 1).sum()
)

repeat_rate = (
    repeat_customers / total_customers * 100
    if total_customers else 0
)

average_customer_value = (
    customer_data["customer_value"].mean()
    if total_customers else 0
)

total_customer_revenue = customer_data["customer_value"].sum()

# ==========================================
# 8. CUSTOMER OVERVIEW
# ==========================================

st.subheader("Customer Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Customers",
    f"{total_customers:,}"
)

col2.metric(
    "Repeat Customers",
    f"{repeat_customers:,}"
)

col3.metric(
    "Repeat Purchase Rate",
    f"{repeat_rate:.2f}%"
)

col4.metric(
    "Average Customer Value",
    f"₹{average_customer_value:,.0f}"
)

st.caption(
    f"Delivered order value from selected customers: "
    f"₹{total_customer_revenue / 10000000:.2f} Cr"
)

st.divider()

# ==========================================
# 9. ONE-TIME VS REPEAT CUSTOMERS
# ==========================================

st.subheader("One-Time vs Repeat Customers")

repeat_summary = pd.DataFrame({
    "Customer Type": ["One-Time Customers", "Repeat Customers"],
    "Customers": [one_time_customers, repeat_customers]
})

fig_repeat = px.pie(
    repeat_summary,
    names="Customer Type",
    values="Customers",
    hole=0.55,
    color_discrete_sequence=["#D8A99C", "#A9C4AC"],
    title="Customer Purchase Behaviour"
)

fig_repeat.update_traces(
    textposition="inside",
    textinfo="percent+label"
)

fig_repeat.update_layout(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#59476C"),
    height=420
)

st.plotly_chart(fig_repeat, width="stretch")

st.divider()

# ==========================================
# 10. CUSTOMER ORDER FREQUENCY
# ==========================================

st.subheader("Customer Purchase Frequency")

frequency_summary = pd.DataFrame({
    "Purchase Segment": [
        "One Order",
        "2–3 Orders",
        "4+ Orders"
    ],
    "Customers": [
        int((customer_data["order_count"] == 1).sum()),
        int(customer_data["order_count"].between(2, 3).sum()),
        int((customer_data["order_count"] >= 4).sum())
    ]
})

fig_frequency = px.bar(
    frequency_summary,
    x="Purchase Segment",
    y="Customers",
    color="Purchase Segment",
    color_discrete_sequence=["#D8A99C", "#B9A0D0", "#A9C4AC"],
    title="Customers by Number of Delivered Orders"
)

fig_frequency.update_layout(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#59476C"),
    showlegend=False,
    height=400
)

st.plotly_chart(fig_frequency, width="stretch")

st.divider()

# ==========================================
# 11. MONTHLY ACTIVE CUSTOMERS
# ==========================================

st.subheader("Monthly Active Customers")

monthly_customers = con.execute("""
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_date BETWEEN ? AND ?
    GROUP BY month
    ORDER BY month
""", params).df()

if not monthly_customers.empty:

    fig_monthly = px.line(
        monthly_customers,
        x="month",
        y="active_customers",
        markers=True,
        color_discrete_sequence=["#A78BC2"],
        title="Monthly Unique Customers",
        labels={
            "month": "Month",
            "active_customers": "Active Customers"
        }
    )

    fig_monthly.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )

    fig_monthly.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=420
    )

    st.plotly_chart(fig_monthly, width="stretch")

st.divider()

# ==========================================
# 12. TOP CUSTOMERS
# ==========================================

st.subheader("Top 10 Customers by Order Value")

top_customers = customer_data.nlargest(
    10, "customer_value"
).copy()

top_customers = top_customers.rename(
    columns={
        "customer_id": "Customer ID",
        "order_count": "Delivered Orders",
        "customer_value": "Order Value (₹)"
    }
)

top_customers["Order Value (₹)"] = (
    top_customers["Order Value (₹)"].round(2)
)

top_customers = top_customers[
    ["Customer ID", "Delivered Orders", "Order Value (₹)"]
]

st.dataframe(
    top_customers,
    width="stretch",
    hide_index=True
)

st.divider()

# ==========================================
# 13. STATE-WISE CUSTOMER DISTRIBUTION
# ==========================================

st.subheader("Customer Distribution by State")

state_customers = con.execute("""
    SELECT
        c.state,
        COUNT(DISTINCT o.customer_id) AS total_customers,
        COUNT(o.order_id) AS delivered_orders,
        SUM(o.final_amount) AS order_value
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY c.state
    ORDER BY total_customers DESC
""", params).df()

if not state_customers.empty:

    fig_state = px.bar(
        state_customers.sort_values("total_customers"),
        x="total_customers",
        y="state",
        orientation="h",
        color_discrete_sequence=["#D6AFC4"],
        title="Unique Customers by State",
        labels={
            "total_customers": "Unique Customers",
            "state": "State"
        }
    )

    fig_state.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=550
    )

    st.plotly_chart(fig_state, width="stretch")

st.divider()

# ==========================================
# 14. FOOTER
# ==========================================

st.caption(
    "Repeat customer = customer with more than one delivered order "
    "within the selected date range. "
    "Customer value = sum of delivered order final amounts "
    "within the selected date range."
)
