
import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px

from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Business Insights",
    page_icon="🤖",
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
        MACHINE LEARNING & BUSINESS INTELLIGENCE
    </div>
    <h1 style="color:#45364F; margin-bottom:8px;">
        AI Business Insights
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Discover customer groups, understand purchase behaviour
        and generate data-driven business recommendations.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "This page uses K-Means machine learning and SQL-based business rules. "
    "It runs locally and does not use a paid AI API."
)

# ==========================================
# 5. CUSTOMER DATA FOR MACHINE LEARNING
# ==========================================

st.subheader("AI Customer Segmentation")

st.write(
    "K-Means clustering groups customers using three behavioural features: "
    "Recency, Frequency and Monetary Value (RFM)."
)

customer_data = con.execute("""
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS frequency,
        SUM(final_amount) AS monetary,
        MAX(order_date) AS last_order
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY customer_id
""").df()

if customer_data.empty:
    st.warning("No delivered customer orders are available.")
    st.stop()

customer_data["last_order"] = pd.to_datetime(
    customer_data["last_order"]
)

latest_order_date = pd.to_datetime(
    con.execute("""
        SELECT MAX(order_date)
        FROM orders
    """).fetchone()[0]
)

reference_date = latest_order_date + pd.Timedelta(days=1)

customer_data["recency"] = (
    reference_date - customer_data["last_order"]
).dt.days

customer_data = customer_data[
    ["customer_id", "recency", "frequency", "monetary"]
].copy()

customer_data = customer_data.replace(
    [np.inf, -np.inf], np.nan
).dropna()

customer_data = customer_data[
    (customer_data["recency"] >= 0) &
    (customer_data["frequency"] > 0) &
    (customer_data["monetary"] > 0)
].copy()

if len(customer_data) < 3:
    st.warning("Not enough customer records for clustering.")
    st.stop()

# ==========================================
# 6. MACHINE LEARNING CONTROLS
# ==========================================

st.markdown("### Model Settings")

n_clusters = st.slider(
    "Choose Number of Customer Groups",
    min_value=3,
    max_value=6,
    value=5,
    step=1
)

st.caption(
    "Changing the number of groups retrains the K-Means model."
)

# ==========================================
# 7. FEATURE SCALING
# ==========================================

features = customer_data[
    ["recency", "frequency", "monetary"]
].copy()

# Log transformation reduces the effect of extreme values.
features = np.log1p(features)

scaler = StandardScaler()

scaled_features = scaler.fit_transform(features)

# ==========================================
# 8. K-MEANS MODEL
# ==========================================

model = KMeans(
    n_clusters=n_clusters,
    random_state=42,
    n_init=10
)

customer_data["cluster"] = model.fit_predict(
    scaled_features
)

customer_data["cluster_label"] = (
    "Cluster " + customer_data["cluster"].astype(str)
)

# ==========================================
# 9. CUSTOMER SEGMENT SUMMARY
# ==========================================

cluster_summary = customer_data.groupby(
    "cluster_label"
).agg(
    total_customers=("customer_id", "count"),
    average_recency=("recency", "mean"),
    average_frequency=("frequency", "mean"),
    average_monetary=("monetary", "mean"),
    total_revenue=("monetary", "sum")
).reset_index()

cluster_summary["average_recency"] = (
    cluster_summary["average_recency"].round(1)
)

cluster_summary["average_frequency"] = (
    cluster_summary["average_frequency"].round(2)
)

cluster_summary["average_monetary"] = (
    cluster_summary["average_monetary"].round(2)
)

cluster_summary["total_revenue"] = (
    cluster_summary["total_revenue"].round(2)
)

# ==========================================
# 10. CUSTOMER SEGMENT KPIs
# ==========================================

total_customers = len(customer_data)

total_clusters = customer_data["cluster"].nunique()

average_customer_value = customer_data["monetary"].mean()

highest_value_cluster = cluster_summary.loc[
    cluster_summary["average_monetary"].idxmax()
]

most_recent_cluster = cluster_summary.loc[
    cluster_summary["average_recency"].idxmin()
]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Customers Analysed",
    f"{total_customers:,}"
)

c2.metric(
    "Customer Groups",
    f"{total_clusters}"
)

c3.metric(
    "Average Customer Value",
    f"₹{average_customer_value:,.0f}"
)

c4.metric(
    "Highest Value Group",
    highest_value_cluster["cluster_label"]
)

st.divider()

# ==========================================
# 11. CUSTOMER CLUSTER VISUALIZATION
# ==========================================

st.subheader("Customer Behaviour Clusters")

fig_clusters = px.scatter(
    customer_data,
    x="frequency",
    y="monetary",
    color="cluster_label",
    hover_data=[
        "customer_id",
        "recency",
        "frequency",
        "monetary"
    ],
    log_x=True,
    log_y=True,
    title="Customer Segmentation: Purchase Frequency vs Customer Value",
    labels={
        "frequency": "Delivered Order Frequency (log scale)",
        "monetary": "Customer Value ₹ (log scale)",
        "cluster_label": "Customer Group"
    },
    color_discrete_sequence=[
        "#B9A0D0",
        "#D8A99C",
        "#A9C4AC",
        "#E7CFA5",
        "#B6C8DC",
        "#D6AFC4"
    ]
)

fig_clusters.update_layout(
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#59476C"),
    height=550
)

st.plotly_chart(fig_clusters, width="stretch")

st.caption(
    "Each point represents one customer. The model uses Recency, "
    "Frequency and Monetary Value; the chart displays Frequency "
    "and Monetary Value. Both chart axes use logarithmic scales."
)

st.divider()

# ==========================================
# 12. CLUSTER PROFILE TABLE
# ==========================================

st.subheader("Customer Group Profiles")

display_summary = cluster_summary.rename(
    columns={
        "cluster_label": "Customer Group",
        "total_customers": "Total Customers",
        "average_recency": "Average Recency (Days)",
        "average_frequency": "Average Orders",
        "average_monetary": "Average Customer Value (₹)",
        "total_revenue": "Total Customer Value (₹)"
    }
)

st.dataframe(
    display_summary,
    width="stretch",
    hide_index=True
)

st.divider()

# ==========================================
# 13. BUSINESS DATA FOR INSIGHTS
# ==========================================

category_data = con.execute("""
    SELECT
        p.category,
        SUM(oi.item_revenue) AS revenue,
        SUM(oi.item_revenue - oi.item_cost) AS profit
    FROM order_items oi
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
    GROUP BY p.category
""").df()

category_data["profit_margin"] = (
    category_data["profit"] /
    category_data["revenue"].replace(0, np.nan) * 100
)

return_data = con.execute("""
    SELECT
        return_reason,
        COUNT(*) AS total_returns
    FROM returns
    GROUP BY return_reason
    ORDER BY total_returns DESC
""").df()

shipping_data = con.execute("""
    SELECT
        s.shipping_method,
        COUNT(*) AS total_shipments,
        COUNT(*) FILTER (
            WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
        ) AS delayed_shipments
    FROM shipments s
    JOIN orders o
        ON s.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY s.shipping_method
""").df()

shipping_data["delay_rate"] = (
    shipping_data["delayed_shipments"] /
    shipping_data["total_shipments"] * 100
)

payment_data = con.execute("""
    SELECT
        payment_method,
        COUNT(*) FILTER (
            WHERE payment_status = 'Success'
        ) AS successful,
        COUNT(*) FILTER (
            WHERE payment_status = 'Failed'
        ) AS failed
    FROM payments
    GROUP BY payment_method
""").df()

payment_data["success_rate"] = (
    payment_data["successful"] /
    (payment_data["successful"] + payment_data["failed"])
    .replace(0, np.nan) * 100
)

# ==========================================
# 14. AUTOMATED BUSINESS INSIGHTS
# ==========================================

st.subheader("Automated Business Insights")

st.write(
    "The following observations are generated from "
    "the dataset's actual business metrics."
)

# Insight 1: Highest value customer group

st.markdown("#### 1. Highest Value Customer Group")

st.info(
    f"{highest_value_cluster['cluster_label']} has the highest "
    f"average customer value at "
    f"₹{highest_value_cluster['average_monetary']:,.2f}. "
    f"It contains {int(highest_value_cluster['total_customers']):,} customers."
)

# Insight 2: Recently active customer group

st.markdown("#### 2. Recently Active Customer Group")

st.info(
    f"{most_recent_cluster['cluster_label']} has the lowest average "
    f"recency at {most_recent_cluster['average_recency']:.1f} days. "
    f"These customers have purchased more recently on average."
)

# Insight 3: Lowest profitability category

st.markdown("#### 3. Category Profitability")

if not category_data.empty:

    lowest_margin = category_data.loc[
        category_data["profit_margin"].idxmin()
    ]

    highest_margin = category_data.loc[
        category_data["profit_margin"].idxmax()
    ]

    st.info(
        f"{lowest_margin['category']} has the lowest product profit "
        f"margin at {lowest_margin['profit_margin']:.2f}%. "
        f"Review product costs, discounts and pricing in this category."
    )

    st.success(
        f"{highest_margin['category']} has the highest product profit "
        f"margin at {highest_margin['profit_margin']:.2f}%. "
        f"Study its pricing and cost structure for possible lessons "
        f"for other categories."
    )

# Insight 4: Return reasons

st.markdown("#### 4. Customer Return Reasons")

if not return_data.empty:

    top_return = return_data.iloc[0]

    st.warning(
        f"'{top_return['return_reason']}' is the most frequent "
        f"return reason, with {int(top_return['total_returns']):,} "
        f"return records. Investigate this issue to reduce returns."
    )

# Insight 5: Delivery performance

st.markdown("#### 5. Delivery Performance")

if not shipping_data.empty:

    worst_shipping = shipping_data.loc[
        shipping_data["delay_rate"].idxmax()
    ]

    st.warning(
        f"{worst_shipping['shipping_method']} has the highest "
        f"delivery delay rate at {worst_shipping['delay_rate']:.2f}%. "
        f"Review its delivery process and logistics performance."
    )

# Insight 6: Payment performance

st.markdown("#### 6. Payment Performance")

comparable_payments = payment_data[
    (payment_data["payment_method"] != "COD") &
    (payment_data["success_rate"].notna())
]

if not comparable_payments.empty:

    lowest_payment = comparable_payments.loc[
        comparable_payments["success_rate"].idxmin()
    ]

    st.warning(
        f"{lowest_payment['payment_method']} has the lowest "
        f"payment attempt success rate among non-COD methods "
        f"at {lowest_payment['success_rate']:.2f}%. "
        f"Investigate payment failures for this method."
    )

st.divider()

# ==========================================
# 15. CUSTOMER GROUP FILTER
# ==========================================

st.subheader("Explore Individual Customer Groups")

selected_cluster = st.selectbox(
    "Select Customer Group",
    sorted(customer_data["cluster_label"].unique())
)

selected_customers = customer_data[
    customer_data["cluster_label"] == selected_cluster
].copy()

selected_customers = selected_customers.sort_values(
    "monetary", ascending=False
)

st.write(
    f"Customers in {selected_cluster}: "
    f"{len(selected_customers):,}"
)

customer_display = selected_customers.rename(
    columns={
        "customer_id": "Customer ID",
        "recency": "Recency (Days)",
        "frequency": "Delivered Orders",
        "monetary": "Customer Value (₹)",
        "cluster_label": "Customer Group"
    }
)

st.dataframe(
    customer_display[
        [
            "Customer ID",
            "Recency (Days)",
            "Delivered Orders",
            "Customer Value (₹)",
            "Customer Group"
        ]
    ].round(2),
    width="stretch",
    hide_index=True
)

st.divider()

# ==========================================
# 16. MODEL INFORMATION
# ==========================================

with st.expander("How does this machine-learning model work?"):

    st.markdown("""
    **Algorithm:** K-Means Clustering

    **Input features:**
    - Recency: Days since the customer's last delivered order.
    - Frequency: Number of distinct delivered orders.
    - Monetary: Total value of delivered orders.

    **Preprocessing:**
    - Log transformation using `log1p()`.
    - Standardization using `StandardScaler`.

    **Model configuration:**
    - Number of clusters: Selected by the user.
    - Random state: 42.
    - Initializations: 10.

    **Purpose:**

    K-Means groups customers with similar purchasing behaviour.
    Businesses can use these groups to plan customer retention,
    loyalty campaigns and marketing strategies.

    Cluster numbers are arbitrary identifiers, not customer rankings.
    The model discovers patterns; it does not prove why customers behave
    in a particular way.
    """)

# ==========================================
# 17. FOOTER
# ==========================================

st.caption(
    "Machine-learning results are exploratory and depend on "
    "the selected number of clusters. Business recommendations "
    "are rule-based observations, not causal predictions."
)
