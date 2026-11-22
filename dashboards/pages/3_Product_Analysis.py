
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Product Analysis",
    page_icon="📦",
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
        Product Analysis
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Explore product revenue, profitability, sales volume
        and product return patterns.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Product metrics are calculated from delivered orders "
    "in a synthetic Indian ecommerce dataset."
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
# 6. PRODUCT KPI DATA
# ==========================================

product_kpi = con.execute("""
    SELECT
        COALESCE(SUM(oi.item_revenue), 0) AS product_revenue,
        COALESCE(SUM(oi.item_cost), 0) AS product_cost,
        COALESCE(
            SUM(oi.item_revenue - oi.item_cost), 0
        ) AS product_profit,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        COUNT(DISTINCT oi.product_id) AS products_sold
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

revenue = product_kpi["product_revenue"]
profit = product_kpi["product_profit"]

profit_margin = (
    profit / revenue * 100 if revenue else 0
)

# ==========================================
# 7. PRODUCT KPI CARDS
# ==========================================

st.subheader("Product Performance Overview")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Product Revenue",
    f"₹{revenue / 10000000:.2f} Cr"
)

c2.metric(
    "Product Profit",
    f"₹{profit / 10000000:.2f} Cr"
)

c3.metric(
    "Profit Margin",
    f"{profit_margin:.2f}%"
)

c4.metric(
    "Units Sold",
    f"{int(product_kpi['units_sold']):,}"
)

c5.metric(
    "Products Sold",
    f"{int(product_kpi['products_sold']):,}"
)

st.divider()

# ==========================================
# 8. CATEGORY PERFORMANCE
# ==========================================

st.subheader("Category-wise Performance")

category = con.execute("""
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

if not category.empty:

    category["profit_margin"] = (
        category["product_profit"] /
        category["product_revenue"].replace(0, pd.NA) * 100
    ).fillna(0)

    left, right = st.columns(2)

    with left:
        fig_revenue = px.bar(
            category.sort_values("product_revenue"),
            x="product_revenue",
            y="category",
            orientation="h",
            color_discrete_sequence=["#B9A0D0"],
            title="Revenue by Category",
            labels={
                "product_revenue": "Product Revenue (₹)",
                "category": "Category"
            }
        )

        fig_revenue.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        fig_revenue.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=550
        )

        st.plotly_chart(fig_revenue, width="stretch")

    with right:
        fig_profit = px.bar(
            category.sort_values("product_profit"),
            x="product_profit",
            y="category",
            orientation="h",
            color_discrete_sequence=["#A9C4AC"],
            title="Profit by Category",
            labels={
                "product_profit": "Product Profit (₹)",
                "category": "Category"
            }
        )

        fig_profit.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        fig_profit.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=550
        )

        st.plotly_chart(fig_profit, width="stretch")

st.divider()

# ==========================================
# 9. TOP 10 PRODUCTS BY REVENUE
# ==========================================

st.subheader("Top 10 Products by Revenue")

top_products = con.execute("""
    SELECT
        oi.product_id,
        p.category,
        SUM(oi.quantity) AS units_sold,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.item_revenue - oi.item_cost) AS product_profit
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY oi.product_id, p.category
    ORDER BY product_revenue DESC
    LIMIT 10
""", params).df()

if not top_products.empty:

    fig_top = px.bar(
        top_products.sort_values("product_revenue"),
        x="product_revenue",
        y="product_id",
        orientation="h",
        color_discrete_sequence=["#D8A99C"],
        title="Top 10 Products by Product Revenue",
        labels={
            "product_revenue": "Product Revenue (₹)",
            "product_id": "Product ID"
        },
        hover_data=["category", "units_sold", "product_profit"]
    )

    fig_top.update_xaxes(
        tickprefix="₹",
        tickformat=",.0f"
    )

    fig_top.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=480
    )

    st.plotly_chart(fig_top, width="stretch")

st.divider()

# ==========================================
# 10. LOWEST PROFIT PRODUCTS
# ==========================================

st.subheader("Products with Lowest Profit")

low_profit = con.execute("""
    SELECT
        oi.product_id,
        p.category,
        SUM(oi.quantity) AS units_sold,
        SUM(oi.item_revenue) AS product_revenue,
        SUM(oi.item_cost) AS product_cost,
        SUM(oi.item_revenue - oi.item_cost) AS product_profit
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?
    GROUP BY oi.product_id, p.category
    ORDER BY product_profit ASC
    LIMIT 10
""", params).df()

if not low_profit.empty:

    fig_low = px.bar(
        low_profit.sort_values("product_profit"),
        x="product_profit",
        y="product_id",
        orientation="h",
        color_discrete_sequence=["#D6AFC4"],
        title="10 Products with Lowest Product Profit",
        labels={
            "product_profit": "Product Profit (₹)",
            "product_id": "Product ID"
        },
        hover_data=["category", "units_sold", "product_revenue"]
    )

    fig_low.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=480
    )

    st.plotly_chart(fig_low, width="stretch")

st.caption(
    "Low profit does not necessarily mean a product is loss-making. "
    "Check the displayed profit values to identify negative-profit products."
)

st.divider()

# ==========================================
# 11. CATEGORY RETURN RATE
# ==========================================

st.subheader("Product Return Rate by Category")

return_analysis = con.execute("""
    WITH eligible_lines AS (
        SELECT DISTINCT
            oi.order_id,
            oi.product_id,
            p.category
        FROM order_items oi
        JOIN orders o
            ON oi.order_id = o.order_id
        JOIN products p
            ON oi.product_id = p.product_id
        WHERE o.order_status IN ('Delivered', 'Returned')
          AND o.order_date BETWEEN ? AND ?
    ),

    returned_lines AS (
        SELECT DISTINCT
            r.order_id,
            r.product_id
        FROM returns r
        JOIN orders o
            ON r.order_id = o.order_id
        WHERE o.order_status IN ('Delivered', 'Returned')
          AND o.order_date BETWEEN ? AND ?
    )

    SELECT
        e.category,
        COUNT(*) AS eligible_product_lines,
        COUNT(r.order_id) AS returned_product_lines,
        ROUND(
            COUNT(r.order_id) * 100.0 /
            NULLIF(COUNT(*), 0), 2
        ) AS return_rate
    FROM eligible_lines e
    LEFT JOIN returned_lines r
        ON e.order_id = r.order_id
       AND e.product_id = r.product_id
    GROUP BY e.category
    ORDER BY return_rate DESC
""", params + params).df()

if not return_analysis.empty:

    fig_returns = px.bar(
        return_analysis.sort_values("return_rate"),
        x="return_rate",
        y="category",
        orientation="h",
        color_discrete_sequence=["#D8A99C"],
        title="Product-Line Return Rate by Category",
        labels={
            "return_rate": "Return Rate (%)",
            "category": "Category"
        },
        hover_data=[
            "eligible_product_lines",
            "returned_product_lines"
        ]
    )

    fig_returns.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=550
    )

    st.plotly_chart(fig_returns, width="stretch")

st.divider()

# ==========================================
# 12. CATEGORY PERFORMANCE TABLE
# ==========================================

st.subheader("Detailed Product Category Report")

if not category.empty:

    display_category = category.copy()

    display_category = display_category.rename(
        columns={
            "category": "Product Category",
            "product_revenue": "Product Revenue (₹)",
            "product_cost": "Product Cost (₹)",
            "product_profit": "Product Profit (₹)",
            "units_sold": "Units Sold",
            "products_sold": "Products Sold",
            "profit_margin": "Profit Margin (%)"
        }
    )

    st.dataframe(
        display_category.round(2),
        width="stretch",
        hide_index=True
    )

st.caption(
    "Revenue, cost and profit are based on delivered order items. "
    "Return rate is calculated at distinct order-product-line level "
    "for Delivered and Returned orders. It is a project-specific metric."
)
