
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Indian Ecommerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. PREMIUM LIGHT THEME
# ==========================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #F8F5EF 0%,
        #F2EEF8 50%,
        #F8F0EA 100%
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

section[data-testid="stSidebar"] {
    background: #EEE8F4;
    border-right: 1px solid #E0D6E9;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.78);
    border: 1px solid #E8DDEA;
    border-radius: 18px;
    padding: 20px 16px;
    box-shadow: 0 5px 18px rgba(89,68,105,0.06);
    min-height: 115px;
}

div[data-testid="stMetricLabel"] {
    color: #776A81;
    font-size: 14px;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #59476C;
    font-weight: 700;
}

div[data-testid="stPlotlyChart"],
div[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.72);
    border-radius: 18px;
    padding: 10px;
    border: 1px solid #E8DDEA;
}

.stButton > button {
    background: linear-gradient(90deg, #B9A0D0, #D8A99C);
    color: #382C43;
    border: none;
    border-radius: 12px;
    font-weight: 600;
}

div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input {
    background: #FFFDF9;
    border-radius: 10px;
    border-color: #DED2E5;
}

hr {
    border-color: #E4D9E8;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = (
    BASE_DIR
    / "database"
    / "ecommerce_analytics.duckdb"
)

# ==========================================
# 4. DATABASE CONNECTION
# ==========================================

@st.cache_resource
def get_connection():
    return duckdb.connect(
        str(DB_PATH),
        read_only=True
    )


con = get_connection()


@st.cache_data
def get_date_range():
    return con.execute("""
        SELECT
            MIN(order_date),
            MAX(order_date)
        FROM orders
    """).fetchone()


min_date, max_date = get_date_range()


if min_date is None or max_date is None:
    st.error("No order dates found in the database.")
    st.stop()



# ==========================================
# 5. DASHBOARD HEADER
# ==========================================

header_html = """
<div style="
    background: linear-gradient(110deg, #E8DDF7, #F9DFD2);
    padding: 32px;
    border-radius: 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 25px rgba(90,65,100,0.08);
">

    <div style="
        font-size: 13px;
        color: #725F80;
        letter-spacing: 2px;
        font-weight: 700;
    ">
        BUSINESS INTELLIGENCE PLATFORM
    </div>

    <h1 style="
        color: #45364F;
        font-size: 32px;
        margin: 12px 0 8px 0;
    ">
        Ecommerce Analytics Dashboard
    </h1>

    <p style="
        color: #6D5D73;
        font-size: 15px;
        margin-bottom: 0;
    ">
        Explore sales, customers, products and business
        performance through interactive analytics.
    </p>

</div>
"""

st.html(header_html)


st.caption(
    "Portfolio project based on a synthetic Indian ecommerce dataset. "
    "Figures do not represent actual company transactions."
)


# ==========================================
# 6. SIDEBAR FILTERS
# ==========================================

st.sidebar.markdown("## Dashboard Filters")

st.sidebar.caption("Choose a date range to explore business performance.")

date_range = st.sidebar.date_input(
    "Select Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

if len(date_range) == 2:

    start_date, end_date = date_range

elif len(date_range) == 1:

    start_date = date_range[0]
    end_date = date_range[0]

else:

    st.warning("Please select a date range.")
    st.stop()


if start_date > end_date:
    st.error("Start date cannot be after end date.")
    st.stop()


st.sidebar.divider()

st.sidebar.markdown("### Selected Period")

st.sidebar.write(
    f"**From:** {start_date.strftime('%d %b %Y')}"
)

st.sidebar.write(
    f"**To:** {end_date.strftime('%d %b %Y')}"
)


# ==========================================
# 7. PLOTLY CHART THEME
# ==========================================

CHART_COLORS = [
    "#B9A0D0",
    "#D8A99C",
    "#A9C4AC",
    "#E7CFA5",
    "#B6C8DC",
    "#D6AFC4",
    "#A9B6A4"
]


def style_chart(fig, height=400):

    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(
            family="Trebuchet MS",
            color="#59476C",
            size=12
        ),
        title_font=dict(
            size=17,
            color="#453B50"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=30
        ),
        hoverlabel=dict(
            bgcolor="#FFFDF9",
            font_color="#453B50"
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0)"
        )
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#EAE2ED",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EAE2ED",
        zeroline=False
    )

    return fig


# ==========================================
# 8. KPI CALCULATIONS
# ==========================================

kpi_query = """
SELECT
    COUNT(*) AS delivered_orders,
    COALESCE(SUM(final_amount), 0) AS delivered_order_value,
    AVG(final_amount) AS average_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers

FROM orders

WHERE order_status = 'Delivered'
AND order_date BETWEEN ? AND ?
"""

kpis = con.execute(
    kpi_query,
    [start_date, end_date]
).df().iloc[0]


profit_query = """
SELECT
    COALESCE(
        SUM(oi.item_revenue - oi.item_cost),
        0
    ) AS product_profit

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

WHERE o.order_status = 'Delivered'
AND o.order_date BETWEEN ? AND ?
"""

profit = con.execute(
    profit_query,
    [start_date, end_date]
).fetchone()[0]


# ==========================================
# 9. BUSINESS OVERVIEW KPI CARDS
# ==========================================

st.subheader("Business Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Delivered Orders",
    f"{int(kpis['delivered_orders']):,}"
)

col2.metric(
    "Order Value",
    f"₹{kpis['delivered_order_value'] / 10000000:.2f} Cr"
)

aov = kpis["average_order_value"]

col3.metric(
    "Average Order Value",
    f"₹{aov:,.0f}" if pd.notna(aov) else "₹0"
)

col4.metric(
    "Unique Customers",
    f"{int(kpis['unique_customers']):,}"
)

col5.metric(
    "Product Profit",
    f"₹{profit / 10000000:.2f} Cr"
)

st.divider()


# ==========================================
# 10. MONTHLY SALES PERFORMANCE
# ==========================================

st.subheader("Monthly Sales Performance")

monthly_query = """
SELECT
    DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS delivered_orders,
    SUM(final_amount) AS order_value

FROM orders

WHERE order_status = 'Delivered'
AND order_date BETWEEN ? AND ?

GROUP BY month
ORDER BY month
"""

monthly = con.execute(
    monthly_query,
    [start_date, end_date]
).df()


if not monthly.empty:

    fig_monthly = px.line(
        monthly,
        x="month",
        y="order_value",
        markers=True,
        color_discrete_sequence=["#A78BC2"],
        labels={
            "month": "Month",
            "order_value": "Order Value (₹)"
        },
        title="Monthly Delivered Order Value"
    )

    fig_monthly.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )

    fig_monthly.update_yaxes(
        tickprefix="₹",
        tickformat=",.0f"
    )

    fig_monthly = style_chart(fig_monthly, 420)

    st.plotly_chart(
        fig_monthly,
        width="stretch"
    )

else:

    st.info("No sales data available for this date range.")


# ==========================================
# 11. PRODUCT CATEGORY PERFORMANCE
# ==========================================

st.subheader("Product Category Performance")

category_query = """
SELECT
    p.category,

    SUM(oi.item_revenue) AS product_revenue,

    SUM(oi.item_revenue - oi.item_cost)
        AS product_profit,

    SUM(oi.quantity) AS units_sold

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN products p
    ON oi.product_id = p.product_id

WHERE o.order_status = 'Delivered'
AND o.order_date BETWEEN ? AND ?

GROUP BY p.category

ORDER BY product_revenue DESC
"""

category = con.execute(
    category_query,
    [start_date, end_date]
).df()


if not category.empty:

    left, right = st.columns(2)

    # Revenue chart

    with left:

        fig_revenue = px.bar(
            category.sort_values("product_revenue"),
            x="product_revenue",
            y="category",
            orientation="h",
            color_discrete_sequence=["#B9A0D0"],
            title="Revenue by Product Category",
            labels={
                "product_revenue": "Revenue (₹)",
                "category": "Category"
            }
        )

        fig_revenue.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        fig_revenue = style_chart(fig_revenue, 550)

        st.plotly_chart(
            fig_revenue,
            width="stretch"
        )

    # Profit chart

    with right:

        fig_profit = px.bar(
            category.sort_values("product_profit"),
            x="product_profit",
            y="category",
            orientation="h",
            color_discrete_sequence=["#A9C4AC"],
            title="Profit by Product Category",
            labels={
                "product_profit": "Profit (₹)",
                "category": "Category"
            }
        )

        fig_profit.update_xaxes(
            tickprefix="₹",
            tickformat=",.0f"
        )

        fig_profit = style_chart(fig_profit, 550)

        st.plotly_chart(
            fig_profit,
            width="stretch"
        )

else:

    st.info("No category data available for this date range.")


# ==========================================
# 12. ORDER STATUS DISTRIBUTION
# ==========================================

st.subheader("Order Status Distribution")

status_query = """
SELECT
    order_status,
    COUNT(*) AS total_orders

FROM orders

WHERE order_date BETWEEN ? AND ?

GROUP BY order_status

ORDER BY total_orders DESC
"""

status = con.execute(
    status_query,
    [start_date, end_date]
).df()


if not status.empty:

    fig_status = px.pie(
        status,
        names="order_status",
        values="total_orders",
        hole=0.55,
        color_discrete_sequence=CHART_COLORS,
        title="Orders by Status"
    )

    fig_status.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig_status = style_chart(fig_status, 450)

    st.plotly_chart(
        fig_status,
        width="stretch"
    )

else:

    st.info("No order status data available.")


# ==========================================
# 13. CATEGORY PERFORMANCE TABLE
# ==========================================

st.subheader("Category Performance Details")

if not category.empty:

    display_category = category.copy()

    display_category["product_revenue"] = (
        display_category["product_revenue"].round(2)
    )

    display_category["product_profit"] = (
        display_category["product_profit"].round(2)
    )

    display_category = display_category.rename(
        columns={
            "category": "Product Category",
            "product_revenue": "Product Revenue (₹)",
            "product_profit": "Product Profit (₹)",
            "units_sold": "Units Sold"
        }
    )

st.dataframe(
    display_category,
    width="stretch",
    hide_index=True,
    height=350,
    column_config={
        "Product Category": st.column_config.TextColumn(
            "Product Category"
        ),
        "Product Revenue (₹)": st.column_config.NumberColumn(
            "Product Revenue (₹)",
            format="₹%.2f"
        ),
        "Product Profit (₹)": st.column_config.NumberColumn(
            "Product Profit (₹)",
            format="₹%.2f"
        ),
        "Units Sold": st.column_config.NumberColumn(
            "Units Sold",
            format="%d"
        )
    }
)


# ==========================================
# 14. FOOTER
# ==========================================

st.divider()

st.html(
    """
    <div style="
        text-align: center;
        color: #897D91;
        font-size: 13px;
        padding: 15px;
    ">
        Indian Ecommerce Analytics |
        Built with Python, DuckDB, Pandas,
        Plotly and Streamlit
    </div>
    """
)
