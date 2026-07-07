import pandas as pd
import requests
import streamlit as st

from auth import API_BASE_URL, auth_headers, require_auth


require_auth()

st.title("Governance Analytics")

st.caption(
    "Monitor system usage, model performance, and governance KPIs."
)

st.divider()

response = requests.get(
    f"{API_BASE_URL}/analytics/",
    headers=auth_headers()
)

if response.status_code == 200:
    analytics = response.json()

    st.subheader("Core Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Requests",
            analytics["total_requests"]
        )

    with col2:
        st.metric(
            "AI Requests",
            analytics["ai_requests"]
        )

    with col3:
        st.metric(
            "Manual Requests",
            analytics["manual_requests"]
        )

    st.divider()

    st.subheader("Content Metrics")

    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            "Average Prompt Length",
            analytics["average_prompt_length"]
        )

    with col5:
        st.metric(
            "Average Response Length",
            analytics["average_response_length"]
        )

    st.divider()

    st.subheader("Reliability Metrics")

    col6, col7 = st.columns(2)

    with col6:
        st.metric(
            "Success Rate (%)",
            analytics["success_rate"]
        )

    with col7:
        st.metric(
            "Failure Rate (%)",
            analytics["failure_rate"]
        )

    st.divider()

    st.subheader("Request Distribution")

    chart_data = pd.DataFrame(
        {
            "Metric": [
                "AI Requests",
                "Manual Requests"
            ],
            "Value": [
                analytics["ai_requests"],
                analytics["manual_requests"]
            ]
        }
    )

    st.bar_chart(
        chart_data.set_index("Metric")
    )

else:
    st.error("Unable to load analytics.")

st.divider()

st.subheader("Model Usage Analytics")

model_response = requests.get(
    f"{API_BASE_URL}/analytics/model-usage",
    headers=auth_headers()
)

if model_response.status_code == 200:
    model_data = model_response.json()

    if model_data:
        model_df = pd.DataFrame(model_data)

        st.bar_chart(
            model_df.set_index("model")
        )

        st.markdown("### Model Usage Details")

        st.dataframe(
            model_df,
            width="stretch"
        )

    else:
        st.info("No model usage data available.")

else:
    st.error("Unable to load model usage data.")

st.divider()

st.info(
    "These analytics are generated from stored prompt interactions and provide governance visibility into AI system usage."
)
