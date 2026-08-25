import os
import requests
import streamlit as st
import streamlit.components.v1 as components


API_BASE_URL = os.getenv("API_BASE_URL", "https://ai-governance-dashboard-production-4c62.up.railway.app")
TOKEN_KEY = "access_token"
USER_KEY = "auth_username"


def auth_headers() -> dict[str, str]:
    token = st.session_state.get(TOKEN_KEY)

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def api_get(url: str, **kwargs) -> requests.Response:
    """Authenticated GET that clears session and reruns on 401."""
    response = requests.get(url, headers=auth_headers(), **kwargs)

    if response.status_code == 401:
        _clear_auth()
        st.rerun()

    return response


def _clear_auth() -> None:
    st.session_state.pop(TOKEN_KEY, None)
    st.session_state.pop(USER_KEY, None)


def _render_authenticated_sidebar() -> None:
    with st.sidebar:
        st.title("AI Governance")

        st.page_link("app.py", label="Home")
        st.page_link("pages/Dashboard.py", label="Dashboard")
        st.page_link("pages/Generate.py", label="Generate")
        st.page_link("pages/History.py", label="History")
        st.page_link("pages/Analytics.py", label="Analytics")

        st.divider()

        username = st.session_state.get(USER_KEY)

        if username:
            st.caption(f"Signed in as {username}")

        if st.button("Sign out"):
            _clear_auth()
            st.rerun()


def _render_login_form() -> None:
    st.title("AI Governance")
    
    tab1, tab2, tab3 = st.tabs(["Sign in", "Sign up", "Forgot Password"])

    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password", type="password", key="login_password"
        )
        submitted = st.button("Sign in", type="primary", key="login_submit")

        # Simulate Enter-to-submit without st.form (which injects "This form"
        # ARIA text that flashes briefly during Streamlit widget reconciliation).
        components.html(
            """
            <script>
            (function() {
                const doc = window.parent.document;
                doc.addEventListener('keydown', function handler(e) {
                    if (e.key !== 'Enter') return;
                    const active = doc.activeElement;
                    const tag = active ? active.tagName : '';
                    if (tag !== 'INPUT') return;
                    const btns = doc.querySelectorAll('button[kind="primaryFormSubmit"], button[data-testid="baseButton-primary"]');
                    for (const btn of btns) {
                        if (btn.innerText.trim() === 'Sign in') {
                            btn.click();
                            return;
                        }
                    }
                });
            })();
            </script>
            """,
            height=0,
        )

        if submitted:
            if not username or not password:
                st.warning("Enter a username and password.")
            else:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/auth/login",
                        json={
                            "username": username,
                            "password": password
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        token = response.json()["access_token"]
                        st.session_state[TOKEN_KEY] = token
                        st.session_state[USER_KEY] = username
                        st.rerun()
                    elif response.status_code == 429:
                        st.error("Too many login attempts. Please wait a minute and try again.")
                    elif response.status_code == 401:
                        st.error("Invalid username or password.")
                    else:
                        st.error(f"Login failed: {response.status_code}")
                except requests.RequestException:
                    st.error("Unable to reach the authentication service.")

    with tab2:
        signup_username = st.text_input("Username", key="signup_username")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_submitted = st.button("Create Account", type="primary", key="signup_submit")
        
        if signup_submitted:
            if not signup_username or not signup_email or not signup_password:
                st.warning("All fields are required.")
            else:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/auth/signup",
                        json={
                            "username": signup_username,
                            "email": signup_email,
                            "password": signup_password
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.success("Account created successfully! Please switch to the 'Sign in' tab to log in.")
                    elif response.status_code == 409:
                        st.error(response.json().get("detail", "Username or email already taken."))
                    else:
                        st.error(f"Signup failed: {response.status_code}")
                except requests.RequestException:
                    st.error("Unable to reach the authentication service.")

    with tab3:
        st.write("Enter your email address to receive a password reset code.")
        reset_email = st.text_input("Email", key="reset_email")
        reset_submitted = st.button("Send Reset Code", key="reset_submit")
        
        if reset_submitted:
            if not reset_email:
                st.warning("Please enter your email.")
            else:
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/auth/forgot-password",
                        json={"email": reset_email},
                        timeout=10
                    )
                    if res.status_code == 200:
                        st.success(res.json().get("message", "If this email exists, a code has been sent."))
                        st.info("The OTP verification flow is not fully implemented in this basic UI yet.")
                    else:
                        st.error("Failed to send reset code.")
                except requests.RequestException:
                    st.error("Unable to reach the authentication service.")


def require_auth() -> None:
    if st.session_state.get(TOKEN_KEY):
        _render_authenticated_sidebar()
        return

    _render_login_form()
    st.stop()
