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
        if "login_step" not in st.session_state:
            st.session_state.login_step = "email"

        if st.session_state.login_step == "email":
            email = st.text_input("Email", key="login_email")
            submitted = st.button("Continue", type="primary", key="login_continue")
            
            if submitted:
                if not email:
                    st.warning("Please enter your email.")
                else:
                    st.session_state.login_email_val = email
                    st.session_state.login_step = "password"
                    st.rerun()
                    
            st.divider()
            if st.button("Continue with Google", key="login_google"):
                st.info("Google OAuth flow will be fully implemented in the frontend migration.")
                
        elif st.session_state.login_step == "password":
            st.write(f"Signing in as: **{st.session_state.login_email_val}**")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Back", key="login_back"):
                    st.session_state.login_step = "email"
                    st.rerun()
                    
            password = st.text_input(
                "Password", type="password", key="login_password"
            )
            submitted = st.button("Sign in", type="primary", key="login_submit")

            if submitted:
                if not password:
                    st.warning("Enter a password.")
                else:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/auth/login",
                            json={
                                "email": st.session_state.login_email_val,
                                "password": password
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            token = response.json()["access_token"]
                            st.session_state[TOKEN_KEY] = token
                            st.session_state[USER_KEY] = st.session_state.login_email_val
                            # Clear login state on success
                            st.session_state.pop("login_step", None)
                            st.session_state.pop("login_email_val", None)
                            st.rerun()
                        elif response.status_code == 429:
                            st.error("Too many login attempts. Please wait a minute and try again.")
                        elif response.status_code == 401:
                            st.error("Invalid email or password.")
                        else:
                            st.error(f"Login failed: {response.status_code}")
                    except requests.RequestException:
                        st.error("Unable to reach the authentication service.")

    with tab2:
        signup_first_name = st.text_input("First Name", key="signup_first")
        signup_last_name = st.text_input("Last Name", key="signup_last")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_submitted = st.button("Create Account", type="primary", key="signup_submit")
        
        st.divider()
        if st.button("Continue with Google", key="signup_google"):
            st.info("Google OAuth flow will be fully implemented in the frontend migration.")
            
        if signup_submitted:
            if not signup_first_name or not signup_last_name or not signup_email or not signup_password:
                st.warning("All fields are required.")
            else:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/auth/signup",
                        json={
                            "first_name": signup_first_name,
                            "last_name": signup_last_name,
                            "email": signup_email,
                            "password": signup_password
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.success("Account created successfully! Please switch to the 'Sign in' tab to log in.")
                    elif response.status_code == 409:
                        st.error(response.json().get("detail", "Email already taken."))
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
