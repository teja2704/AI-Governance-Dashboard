import streamlit as st
import requests

st.title("🤖 Generate AI Response")

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
        "🚀 Generate",
        use_container_width=True
    )

if generate_button:

    if not prompt.strip():

        st.warning(
            "Please enter a prompt."
        )

    else:

        with st.spinner(
            "Generating response..."
        ):

            response = requests.post(
                "http://127.0.0.1:8000/prompts/generate",
                json={
                    "prompt": prompt
                }
            )

        if response.status_code == 200:

            result = response.json()

            st.success(
                "Response generated successfully."
            )

            st.divider()

            st.subheader("🤖 AI Response")

            st.text_area(
                "Generated Output",
                value=result["response"],
                height=350,
                disabled=True
            )

        else:

            st.error(
                f"API Error: {response.status_code}"
            )

            st.code(
                response.text
            )

st.divider()

st.info(
    "All generated responses are automatically stored in the database and tracked through the governance dashboard."
)