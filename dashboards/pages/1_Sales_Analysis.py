
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Sales Analysis",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# 2. THEME
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
        Sales Analysis
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Understand revenue trends, profitability and regional sales performance.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption("Analysis uses delivered orders from a synthetic Indian ecommerce dataset.")

# ==========================================
# 5. DATE FILTER
# ==========================================

min_date, max_date = con.execute("""
    SELECT MIN(order_date), MAX(order_date)
    FROM orders
""").fetchone()

min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

start_date, end_date = st.sidebar.date_input(
    "Select Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

if start_date > end_date:
    st.error("Start date cannot be after end date.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.write("**Selected Period**")
st.sidebar.write(f"From: {start_date.strftime('%d %b %Y')}")
st.sidebar.write(f"To: {end_date.strftime('%d %b %Y')}")

params = [start_date, end_date]

# ==========================================
# 6. SALES KPI CALCULATIONS
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
        COALESCE(SUM(oi.item_revenue - oi.item_cost), 0) AS product_profit
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

product_revenue = product_kpi["product_revenue"]
product_profit = product_kpi["product_profit"]

profit_margin = (
    product_profit / product_revenue * 100
    if product_revenue else 0
)

# ==========================================
# 7. KPI CARDS
# ==========================================

st.subheader("Sales Performance Overview")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Delivered Orders",
    f"{int(sales_kpi['delivered_orders']):,}"
)

c2.metric(
    "Order Value",
    f"₹{sales_kpi['order_value'] / 10000000:.2f} Cr"
)

c3.metric(
    "Average Order Value",
    f"₹{sales_kpi['average_order_value']:,.0f}"
    if pd.notna(sales_kpi['average_order_value']) else "₹0"
)

c4.metric(
    "Product Revenue",
    f"₹{product_revenue / 10000000:.2f} Cr"
)

c5.metric(
    "Product Profit",
    f"₹{product_profit / 10000000:.2f} Cr"
)

st.caption(
    f"Product profit margin: {profit_margin:.2f}%"
)

st.divider()

# ==========================================
# 8. MONTHLY SALES TREND
# ==========================================

st.subheader("Monthly Sales Trend")

monthly = con.execute("""
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        COUNT(*) AS delivered_orders,
        SUM(final_amount) AS order_value
    FROM orders
    WHERE order_status = 'Delivered'
      AND order_date BETWEEN ? AND ?
    GROUP BY month
    ORDER BY month
""", params).df()

if not monthly.empty:

    fig_monthly = px.line(
        monthly,
        x="month",
        y="order_value",
        markers=True,
        color_discrete_sequence=["#A78BC2"],
        title="Monthly Delivered Order Value",
        labels={
            "month": "Month",
            "order_value": "Order Value (₹)"
        }
    )

    fig_monthly.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )

    fig_monthly.update_yaxes(
        tickprefix="₹",
        tickformat=",.0f"
    )

    fig_monthly.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=430
    )

    st.plotly_chart(fig_monthly, width="stretch")

# ==========================================
# 9. MONTHLY ORDER VOLUME
# ==========================================

st.subheader("Monthly Delivered Order Volume")

fig_orders = px.bar(
    monthly,
    x="month",
    y="delivered_orders",
    color_discrete_sequence=["#D8A99C"],
    title="Number of Delivered Orders by Month",
    labels={
        "month": "Month",
        "delivered_orders": "Delivered Orders"
    }
)

fig_orders.update_layout(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#59476C"),
    height=400
)

st.plotly_chart(fig_orders, width="stretch")

st.divider()

# ==========================================
# 10. CATEGORY REVENUE
# ==========================================

st.subheader("Revenue by Product Category")

category = con.execute("""
    SELECT
        p.category,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.item_revenue - oi.item_cost) AS product_profit,
        SUM(oi.quantity) AS units_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY p.category
    ORDER BY product_revenue DESC
""", params).df()

if not category.empty:

    left, right = st.columns(2)

    with left:
        fig_category_revenue = px.bar(
            category.sort_values("product_revenue"),
            x="product_revenue",
            y="category",
            orientation="h",
            color_discrete_sequence=["#B9A0D0"],
            title="Product Revenue by Category",
            labels={
                "product_revenue": "Revenue (₹)",
                "category": "Category"
            }
        )

        fig_category_revenue.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=550
        )

        fig_category_revenue.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        st.plotly_chart(fig_category_revenue, width="stretch")

    with right:
        fig_category_profit = px.bar(
            category.sort_values("product_profit"),
            x="product_profit",
            y="category",
            orientation="h",
            color_discrete_sequence=["#A9C4AC"],
            title="Product Profit by Category",
            labels={
                "product_profit": "Profit (₹)",
                "category": "Category"
            }
        )

        fig_category_profit.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=550
        )

        fig_category_profit.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        st.plotly_chart(fig_category_profit, width="stretch")

st.divider()

# ==========================================
# 11. STATE-WISE SALES
# ==========================================

st.subheader("State-wise Sales Performance")

state_sales = con.execute("""
    SELECT
        c.state,
        COUNT(o.order_id) AS delivered_orders,
        SUM(o.final_amount) AS order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY c.state
    ORDER BY order_value DESC
""", params).df()

if not state_sales.empty:

    fig_state = px.bar(
        state_sales.head(10).sort_values("order_value"),
        x="order_value",
        y="state",
        orientation="h",
        color_discrete_sequence=["#D6AFC4"],
        title="Top 10 States by Delivered Order Value",
        labels={
            "order_value": "Order Value (₹)",
            "state": "State"
        }
    )

    fig_state.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=450
    )

    fig_state.update_xaxes(
        tickprefix="₹",
        tickformat=",.0f"
    )

    st.plotly_chart(fig_state, width="stretch")

st.divider()

# ==========================================
# 12. CATEGORY DETAILS TABLE
# ==========================================

st.subheader("Detailed Category Performance")

if not category.empty:

    category_display = category.copy()

    category_display["product_revenue"] = (
        category_display["product_revenue"].round(2)
    )

    category_display["product_profit"] = (
        category_display["product_profit"].round(2)
    )

    category_display = category_display.rename(
        columns={
            "category": "Product Category",
            "product_revenue": "Product Revenue (₹)",
            "product_profit": "Product Profit (₹)",
            "units_sold": "Units Sold"
        }
    )

    st.dataframe(
        category_display,
        width="stretch",
        hide_index=True
    )

st.caption(
    "Note: Order Value includes shipping and tax. "
    "Product Revenue and Product Profit are calculated from delivered order items."
)
