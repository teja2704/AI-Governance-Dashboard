import requests
import streamlit as st

from auth import API_BASE_URL, auth_headers, require_auth


require_auth()

st.title("Generate AI Response")

st.caption(
    "Generate responses using Gemini and automatically store interactions for governance tracking."
)

st.divider()

st.subheader("Prompt Input")

prompt = st.text_area(
    "Enter your prompt",
    height=150,
    placeholder="Example: Explain XGBoost in simple terms..."
)

col1, col2 = st.columns([1, 4])

with col1:
    generate_button = st.button(
        "Generate",
        use_container_width=True
    )

if generate_button:
    if not prompt.strip():
        st.warning("Please enter a prompt.")

    else:
        try:
            with st.spinner("Generating response..."):
                response = requests.post(
                    f"{API_BASE_URL}/prompts/generate",
                    headers=auth_headers(),
                    json={
                        "prompt": prompt
                    },
                    timeout=30
                )
        except requests.RequestException:
            st.error(
                "Unable to reach the generation service. "
                "Please try again shortly."
            )
            st.stop()

        if response.status_code == 200:
            result = response.json()

            st.success("Response generated successfully.")

            st.divider()

            st.subheader("AI Response")

            st.text_area(
                "Generated Output",
                value=result["response"],
                height=350,
                disabled=True
            )

        else:
            error_message = "AI generation failed. Please try again shortly."

            try:
                error_body = response.json()
                detail = error_body.get("detail")

                if isinstance(detail, str):
                    error_message = detail
                elif isinstance(detail, dict):
                    error_message = detail.get("message", error_message)
            except ValueError:
                pass

            st.error(error_message)

st.divider()

st.info(
    "All generated responses are automatically stored in the database and tracked through the governance dashboard."
)
