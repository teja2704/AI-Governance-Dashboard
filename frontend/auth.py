import os
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TOKEN_KEY = "access_token"
USER_KEY = "auth_username"


def auth_headers() -> dict[str, str]:
    token = st.session_state.get(TOKEN_KEY)

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def _clear_auth() -> None:
    st.session_state.pop(TOKEN_KEY, None)
    st.session_state.pop(USER_KEY, None)


def _render_logout() -> None:
    with st.sidebar:
        username = st.session_state.get(USER_KEY)

        if username:
            st.caption(f"Signed in as {username}")

        if st.button("Sign out"):
            _clear_auth()
            st.rerun()


def _render_login_form() -> None:
    st.title("Sign in")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if not submitted:
        return

    if not username or not password:
        st.warning("Enter a username and password.")
        return

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )
    except requests.RequestException:
        st.error("Unable to reach the authentication service.")
        return

    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state[TOKEN_KEY] = token
        st.session_state[USER_KEY] = username
        st.rerun()

    elif response.status_code == 401:
        st.error("Invalid username or password.")

    else:
        st.error(f"Login failed: {response.status_code}")


def require_auth() -> None:
    if st.session_state.get(TOKEN_KEY):
        _render_logout()
        return

    _render_login_form()
    st.stop()
