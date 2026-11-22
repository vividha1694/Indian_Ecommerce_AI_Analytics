
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Operations Analysis",
    page_icon="🚚",
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
        Operations Analysis
    </h1>
    <p style="color:#6D5D73; margin-bottom:0;">
        Monitor payment performance, product returns,
        delivery efficiency and warehouse operations.
    </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Operational metrics are based on a synthetic Indian "
    "ecommerce dataset. Figures do not represent actual company transactions."
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
# 6. PAYMENT KPI DATA
# ==========================================

payment_kpi = con.execute("""
    SELECT
        COUNT(*) AS total_transactions,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Success'
        ) AS successful_payments,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Failed'
        ) AS failed_payments,

        COALESCE(
            SUM(p.amount_paid) FILTER (
                WHERE p.payment_status = 'Success'
            ), 0
        ) AS successful_payment_amount,

        COALESCE(SUM(p.refund_amount), 0) AS payment_refund_amount

    FROM payments p
    JOIN orders o
        ON p.order_id = o.order_id

    WHERE o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

attempts = (
    payment_kpi["successful_payments"] +
    payment_kpi["failed_payments"]
)

payment_success_rate = (
    payment_kpi["successful_payments"] / attempts * 100
    if attempts else 0
)

# ==========================================
# 7. RETURN KPI DATA
# ==========================================

return_kpi = con.execute("""
    SELECT
        COUNT(*) AS total_return_records,

        COUNT(*) FILTER (
            WHERE r.return_status = 'Refund Completed'
        ) AS completed_refunds,

        COUNT(*) FILTER (
            WHERE r.return_status = 'Approved'
        ) AS approved_returns,

        COALESCE(SUM(r.refund_amount), 0) AS return_refund_amount

    FROM returns r
    JOIN orders o
        ON r.order_id = o.order_id

    WHERE o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

# ==========================================
# 8. DELIVERY KPI DATA
# ==========================================

delivery_kpi = con.execute("""
    SELECT
        COUNT(*) AS total_shipments,

        COUNT(*) FILTER (
            WHERE o.order_status = 'Delivered'
        ) AS delivered_orders,

        COUNT(*) FILTER (
            WHERE o.order_status = 'Delivered'
              AND TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
        ) AS delayed_deliveries,

        AVG(s.delivery_days) FILTER (
            WHERE o.order_status = 'Delivered'
        ) AS average_delivery_days

    FROM shipments s
    JOIN orders o
        ON s.order_id = o.order_id

    WHERE o.order_date BETWEEN ? AND ?
""", params).df().iloc[0]

delivered_count = delivery_kpi["delivered_orders"]

delivery_delay_rate = (
    delivery_kpi["delayed_deliveries"] / delivered_count * 100
    if delivered_count else 0
)

# ==========================================
# 9. OPERATIONS OVERVIEW
# ==========================================

st.subheader("Operations Performance Overview")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Payment Success Rate",
    f"{payment_success_rate:.2f}%"
)

c2.metric(
    "Failed Payments",
    f"{int(payment_kpi['failed_payments']):,}"
)

c3.metric(
    "Return Records",
    f"{int(return_kpi['total_return_records']):,}"
)

c4.metric(
    "Delivery Delay Rate",
    f"{delivery_delay_rate:.2f}%"
)

c5.metric(
    "Average Delivery Time",
    f"{delivery_kpi['average_delivery_days']:.2f} days"
    if pd.notna(delivery_kpi["average_delivery_days"])
    else "N/A"
)

st.divider()

# ==========================================
# 10. PAYMENT METHOD ANALYSIS
# ==========================================

st.subheader("Payment Method Performance")

payment_methods = con.execute("""
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
        ) AS success_rate,

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

if not payment_methods.empty:

    left, right = st.columns(2)

    with left:

        fig_payment = px.bar(
            payment_methods.sort_values("successful_payments"),
            x="successful_payments",
            y="payment_method",
            orientation="h",
            color_discrete_sequence=["#B9A0D0"],
            title="Successful Payments by Method",
            labels={
                "successful_payments": "Successful Payments",
                "payment_method": "Payment Method"
            }
        )

        fig_payment.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=500
        )

        st.plotly_chart(fig_payment, width="stretch")

    with right:

        fig_success = px.bar(
            payment_methods.sort_values("success_rate"),
            x="success_rate",
            y="payment_method",
            orientation="h",
            color_discrete_sequence=["#A9C4AC"],
            title="Payment Attempt Success Rate",
            labels={
                "success_rate": "Success Rate (%)",
                "payment_method": "Payment Method"
            }
        )

        fig_success.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=500
        )

        fig_success.update_xaxes(ticksuffix="%")

        st.plotly_chart(fig_success, width="stretch")

st.caption(
    "Payment attempt success rate = successful transactions / "
    "(successful + failed transactions). Pending, refunded and "
    "not-charged transactions are excluded. COD is not directly "
    "comparable to payment gateway methods."
)

st.divider()

# ==========================================
# 11. PAYMENT STATUS DISTRIBUTION
# ==========================================

st.subheader("Payment Status Distribution")

payment_status = con.execute("""
    SELECT
        p.payment_status,
        COUNT(*) AS total_transactions
    FROM payments p
    JOIN orders o
        ON p.order_id = o.order_id
    WHERE o.order_date BETWEEN ? AND ?
    GROUP BY p.payment_status
    ORDER BY total_transactions DESC
""", params).df()

if not payment_status.empty:

    fig_payment_status = px.pie(
        payment_status,
        names="payment_status",
        values="total_transactions",
        hole=0.55,
        color_discrete_sequence=[
            "#A9C4AC",
            "#D8A99C",
            "#B9A0D0",
            "#E7CFA5",
            "#B6C8DC"
        ],
        title="Transactions by Payment Status"
    )

    fig_payment_status.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig_payment_status.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=430
    )

    st.plotly_chart(fig_payment_status, width="stretch")

st.divider()

# ==========================================
# 12. RETURN REASON ANALYSIS
# ==========================================

st.subheader("Product Return Reasons")

return_reasons = con.execute("""
    SELECT
        r.return_reason,
        COUNT(*) AS total_returns,
        SUM(r.refund_amount) AS refund_amount
    FROM returns r
    JOIN orders o
        ON r.order_id = o.order_id
    WHERE o.order_date BETWEEN ? AND ?
    GROUP BY r.return_reason
    ORDER BY total_returns DESC
""", params).df()

if not return_reasons.empty:

    fig_reasons = px.bar(
        return_reasons.sort_values("total_returns"),
        x="total_returns",
        y="return_reason",
        orientation="h",
        color_discrete_sequence=["#D8A99C"],
        title="Returns by Reason",
        labels={
            "total_returns": "Return Records",
            "return_reason": "Return Reason"
        },
        hover_data=["refund_amount"]
    )

    fig_reasons.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=480
    )

    st.plotly_chart(fig_reasons, width="stretch")

st.divider()

# ==========================================
# 13. RETURN STATUS ANALYSIS
# ==========================================

st.subheader("Return and Refund Status")

return_status = con.execute("""
    SELECT
        r.return_status,
        COUNT(*) AS total_records,
        SUM(r.refund_amount) AS refund_amount
    FROM returns r
    JOIN orders o
        ON r.order_id = o.order_id
    WHERE o.order_date BETWEEN ? AND ?
    GROUP BY r.return_status
    ORDER BY total_records DESC
""", params).df()

if not return_status.empty:

    left, right = st.columns(2)

    with left:

        fig_return_status = px.pie(
            return_status,
            names="return_status",
            values="total_records",
            hole=0.55,
            color_discrete_sequence=[
                "#A9C4AC",
                "#B9A0D0",
                "#D8A99C",
                "#E7CFA5"
            ],
            title="Return Status Distribution"
        )

        fig_return_status.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )

        fig_return_status.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=430
        )

        st.plotly_chart(fig_return_status, width="stretch")

    with right:

        st.markdown("#### Refund Amount by Return Status")

        display_returns = return_status.rename(
            columns={
                "return_status": "Return Status",
                "total_records": "Return Records",
                "refund_amount": "Refund Amount (₹)"
            }
        )

        st.dataframe(
            display_returns.round(2),
            width="stretch",
            hide_index=True
        )

st.divider()

# ==========================================
# 14. DELIVERY PERFORMANCE BY SHIPPING METHOD
# ==========================================

st.subheader("Delivery Performance by Shipping Method")

shipping = con.execute("""
    SELECT
        s.shipping_method,

        COUNT(*) AS delivered_shipments,

        COUNT(*) FILTER (
            WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
        ) AS delayed_shipments,

        ROUND(
            AVG(s.delivery_days), 2
        ) AS average_delivery_days,

        ROUND(
            COUNT(*) FILTER (
                WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
            ) * 100.0 / NULLIF(COUNT(*), 0), 2
        ) AS delay_rate

    FROM shipments s
    JOIN orders o
        ON s.order_id = o.order_id

    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?

    GROUP BY s.shipping_method
    ORDER BY delay_rate DESC
""", params).df()

if not shipping.empty:

    left, right = st.columns(2)

    with left:

        fig_shipping = px.bar(
            shipping.sort_values("delay_rate"),
            x="delay_rate",
            y="shipping_method",
            orientation="h",
            color_discrete_sequence=["#D8A99C"],
            title="Delivery Delay Rate by Shipping Method",
            labels={
                "delay_rate": "Delay Rate (%)",
                "shipping_method": "Shipping Method"
            }
        )

        fig_shipping.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=480
        )

        fig_shipping.update_xaxes(ticksuffix="%")

        st.plotly_chart(fig_shipping, width="stretch")

    with right:

        fig_delivery_days = px.bar(
            shipping.sort_values("average_delivery_days"),
            x="average_delivery_days",
            y="shipping_method",
            orientation="h",
            color_discrete_sequence=["#B9A0D0"],
            title="Average Delivery Days",
            labels={
                "average_delivery_days": "Average Days",
                "shipping_method": "Shipping Method"
            }
        )

        fig_delivery_days.update_layout(
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            font=dict(color="#59476C"),
            height=480
        )

        st.plotly_chart(fig_delivery_days, width="stretch")

st.caption(
    "Delivery delay rate uses the supplied delayed_flag field "
    "among delivered orders. It is not independently recalculated "
    "from expected and actual delivery dates."
)

st.divider()

# ==========================================
# 15. WAREHOUSE PERFORMANCE
# ==========================================

st.subheader("Warehouse Delivery Performance")

warehouse = con.execute("""
    SELECT
        s.warehouse_city,

        COUNT(*) AS delivered_shipments,

        COUNT(*) FILTER (
            WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
        ) AS delayed_shipments,

        ROUND(
            AVG(s.delivery_days), 2
        ) AS average_delivery_days,

        ROUND(
            COUNT(*) FILTER (
                WHERE TRY_CAST(s.delayed_flag AS BOOLEAN) = TRUE
            ) * 100.0 / NULLIF(COUNT(*), 0), 2
        ) AS delay_rate

    FROM shipments s
    JOIN orders o
        ON s.order_id = o.order_id

    WHERE o.order_status = 'Delivered'
      AND o.order_date BETWEEN ? AND ?

    GROUP BY s.warehouse_city
    ORDER BY delay_rate DESC
""", params).df()

if not warehouse.empty:

    fig_warehouse = px.bar(
        warehouse.sort_values("delay_rate"),
        x="delay_rate",
        y="warehouse_city",
        orientation="h",
        color_discrete_sequence=["#A9C4AC"],
        title="Delivery Delay Rate by Warehouse",
        labels={
            "delay_rate": "Delay Rate (%)",
            "warehouse_city": "Warehouse"
        },
        hover_data=[
            "delivered_shipments",
            "delayed_shipments",
            "average_delivery_days"
        ]
    )

    fig_warehouse.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#59476C"),
        height=480
    )

    fig_warehouse.update_xaxes(ticksuffix="%")

    st.plotly_chart(fig_warehouse, width="stretch")

    display_warehouse = warehouse.rename(
        columns={
            "warehouse_city": "Warehouse",
            "delivered_shipments": "Delivered Shipments",
            "delayed_shipments": "Delayed Shipments",
            "average_delivery_days": "Average Delivery Days",
            "delay_rate": "Delay Rate (%)"
        }
    )

    st.dataframe(
        display_warehouse,
        width="stretch",
        hide_index=True
    )

st.divider()

# ==========================================
# 16. OPERATIONS SUMMARY
# ==========================================

st.subheader("Operations Summary")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Payment Summary")
    st.write(
        f"Successful payments: "
        f"{int(payment_kpi['successful_payments']):,}"
    )
    st.write(
        f"Failed payments: "
        f"{int(payment_kpi['failed_payments']):,}"
    )
    st.write(
        f"Successful payment amount: "
        f"₹{payment_kpi['successful_payment_amount']:,.2f}"
    )

with col2:
    st.markdown("#### Returns Summary")
    st.write(
        f"Completed refunds: "
        f"{int(return_kpi['completed_refunds']):,}"
    )
    st.write(
        f"Approved returns: "
        f"{int(return_kpi['approved_returns']):,}"
    )
    st.write(
        f"Return-table refund amount: "
        f"₹{return_kpi['return_refund_amount']:,.2f}"
    )

st.divider()

# ==========================================
# 17. FOOTER
# ==========================================

st.caption(
    "Payment amounts and return-table refund amounts are separate "
    "measures and should not be added together. "
    "Delivery performance is calculated using delivered orders only."
)
