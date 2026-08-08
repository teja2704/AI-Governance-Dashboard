import os
import requests
import streamlit as st
import streamlit.components.v1 as components


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

    elif response.status_code == 429:
        st.error("Too many login attempts. Please wait a minute and try again.")

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
