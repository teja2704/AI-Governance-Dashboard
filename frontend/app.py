import requests
import streamlit as st

from auth import API_BASE_URL, auth_headers, require_auth


st.set_page_config(
    page_title="AI Governance Dashboard",
    layout="wide"
)

require_auth()

st.title("AI Governance Dashboard")

st.markdown("""
### AI Monitoring & Governance Platform

Track AI-generated responses, monitor model performance,
analyze prompt history, and evaluate governance metrics.
""")

try:
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

        st.subheader("System Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", analytics["total_requests"])

        with col2:
            st.metric("AI Requests", analytics["ai_requests"])

        with col3:
            st.metric("Success Rate", f'{kpis["success_rate"]}%')

        with col4:
            st.metric("Failed Requests", kpis["failed_requests"])

        st.divider()

        col5, col6 = st.columns(2)

        with col5:
            st.info(
                f"""
### Most Used Model

{kpis["most_used_model"]}
"""
            )

        with col6:
            st.success(
                f"""
### System Status

Operational

Success Rate: {kpis["success_rate"]}%
"""
            )

except Exception:
    st.warning("Backend not available. Start FastAPI server.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Platform Features")

    st.markdown("""
- AI Response Generation
- Prompt History Tracking
- Governance Analytics
- Model Usage Monitoring
- Success & Failure Tracking
- CSV Export
""")

with col2:
    st.subheader("Architecture")

    st.markdown("""
**Backend**
- FastAPI
- SQLAlchemy
- PostgreSQL

**Frontend**
- Streamlit

**AI Model**
- Gemini 2.5 Flash
""")

st.divider()

st.sidebar.title("AI Governance")

st.sidebar.markdown("""
### Navigation

Use the pages below to:

- Dashboard
- Generate
- History
- Analytics
""")
