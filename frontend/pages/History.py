import pandas as pd
import requests
import streamlit as st

from auth import API_BASE_URL, auth_headers, require_auth


require_auth()

st.title("Prompt History")

st.caption(
    "Search, filter, inspect, and export historical AI interactions."
)

st.divider()

response = requests.get(
    f"{API_BASE_URL}/prompts/history",
    headers=auth_headers()
)

if response.status_code == 200:
    history_data = response.json()

    if history_data:
        df = pd.DataFrame(history_data)
        full_df = df.copy()

        st.subheader("Search & Filters")

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=None
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=None
            )

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["timestamp"]
            )

            if start_date:
                df = df[
                    df["timestamp"].dt.date >= start_date
                ]

            if end_date:
                df = df[
                    df["timestamp"].dt.date <= end_date
                ]

        search_term = st.text_input(
            "Search Prompts",
            placeholder="Enter keywords..."
        )

        if search_term:
            df = df[
                df["prompt"]
                .str.contains(
                    search_term,
                    case=False,
                    na=False
                )
            ]

        st.divider()

        st.subheader("Export Data")

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download History CSV",
            data=csv,
            file_name="prompt_history.csv",
            mime="text/csv"
        )

        st.divider()

        st.subheader("Interaction Records")

        if "response" in df.columns:
            df["response_length"] = (
                df["response"]
                .fillna("")
                .astype(str)
                .str.len()
            )

        columns_to_show = [
            "id",
            "prompt",
            "model",
            "status",
            "response_length",
            "timestamp"
        ]

        available_columns = [
            col
            for col in columns_to_show
            if col in df.columns
        ]

        st.dataframe(
            df[available_columns],
            width="stretch"
        )

        if not df.empty:
            st.divider()

            st.subheader("Prompt Detail View")

            selected_id = st.selectbox(
                "Select Prompt ID",
                df["id"].tolist()
            )

            selected_row = full_df[
                full_df["id"] == selected_id
            ].iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Prompt")

                st.text_area(
                    "Prompt",
                    value=str(selected_row["prompt"]),
                    height=150,
                    disabled=True
                )

            with col2:
                st.markdown("### Response")

                response_text = selected_row.get("response")

                if (
                    pd.isna(response_text)
                    or
                    response_text is None
                ):
                    response_text = "No AI response available."

                st.text_area(
                    "Response",
                    value=str(response_text),
                    height=150,
                    disabled=True
                )

            st.divider()

            st.subheader("Metadata")

            meta_col1, meta_col2, meta_col3 = st.columns(3)

            with meta_col1:
                st.metric(
                    "Model",
                    selected_row.get(
                        "model",
                        "N/A"
                    )
                )

            with meta_col2:
                st.metric(
                    "Status",
                    selected_row.get(
                        "status",
                        "N/A"
                    )
                )

            with meta_col3:
                timestamp = selected_row.get(
                    "timestamp",
                    "N/A"
                )

                st.metric(
                    "Timestamp",
                    str(timestamp)
                )

    else:
        st.info("No prompt history available.")

else:
    st.error("Unable to load history.")
