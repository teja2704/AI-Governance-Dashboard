import requests
import streamlit as st

from auth import API_BASE_URL, auth_headers, require_auth


require_auth()

st.title("AI Governance Dashboard")

st.markdown("""
Welcome to the AI Governance Dashboard.

Monitor AI usage, track response quality,
analyze prompt history, and review governance metrics.
""")

analytics_response = requests.get(
    f"{API_BASE_URL}/analytics/",
    headers=auth_headers()
)

kpi_response = requests.get(
    f"{API_BASE_URL}/analytics/dashboard-kpis",
    headers=auth_headers()
)

if (
    analytics_response.status_code == 200
    and
    kpi_response.status_code == 200
):
    analytics = analytics_response.json()
    kpis = kpi_response.json()

    st.divider()

    st.subheader("Governance Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Requests",
            value=analytics["total_requests"]
        )

    with col2:
        st.metric(
            label="AI Requests",
            value=analytics["ai_requests"]
        )

    with col3:
        st.metric(
            label="Manual Requests",
            value=analytics["manual_requests"]
        )

    st.divider()

    st.subheader("Performance Metrics")

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            label="Success Rate (%)",
            value=kpis["success_rate"]
        )

    with col5:
        st.metric(
            label="Failed Requests",
            value=kpis["failed_requests"]
        )

    with col6:
        st.metric(
            label="Longest Response",
            value=kpis["longest_response"]
        )

    st.divider()

    st.subheader("Model Insights")

    col7, col8 = st.columns(2)

    with col7:
        st.info(
            f"""
**Most Used Model**

{kpis["most_used_model"]}
"""
        )

    with col8:
        st.success(
            f"""
**System Health**

Success Rate: {kpis["success_rate"]}%
"""
        )

    st.divider()

    st.subheader("Latest Prompt")

    st.text_area(
        "Most Recent User Prompt",
        value=kpis["latest_prompt"],
        height=120,
        disabled=True
    )

else:
    st.error("Unable to load dashboard data.")
