import os
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment must be set before any backend module is imported so that
# init_db() and the ORM engine pick up the correct SQLite URL.
# ---------------------------------------------------------------------------
TEST_DB_PATH = (
    Path(tempfile.gettempdir()) /
    f"ai_governance_dashboard_tests_{os.getpid()}.db"
)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["AUTH_BOOTSTRAP_USERNAME"] = "admin@example.com"
os.environ["AUTH_BOOTSTRAP_PASSWORD"] = "AdminPassword123!"
os.environ["GEMINI_API_KEY"] = "test-gemini-api-key"

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient



from backend.main import app
from backend.rate_limiter import limiter


LOGIN_URL = "/auth/login"
LOGIN_BODY = {
    "email": os.environ["AUTH_BOOTSTRAP_USERNAME"],
    "password": os.environ["AUTH_BOOTSTRAP_PASSWORD"],
}


class RateLimitTest(unittest.TestCase):
    """Verifies that /auth/login enforces a 5-requests-per-minute limit."""

    @classmethod
    def setUpClass(cls):
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        limiter._storage.reset()

    @classmethod
    def tearDownClass(cls):
        from backend.database.db import engine

        engine.dispose()
        TEST_DB_PATH.unlink(missing_ok=True)

    def test_login_rate_limit(self):
        """
        First 5 requests must succeed (not 429).
        The 6th request must be blocked with a 429 response whose body is
        well-formed JSON and does not look like a raw exception / stack trace.
        """
        with TestClient(app) as client:
            # --- first 5 requests: none should be rate-limited ---
            for i in range(1, 6):
                response = client.post(LOGIN_URL, json=LOGIN_BODY)
                self.assertNotEqual(
                    response.status_code,
                    429,
                    msg=(
                        f"Request {i}/5 was unexpectedly rate-limited "
                        f"(status {response.status_code})."
                    ),
                )

            # --- 6th request: must be blocked ---
            response = client.post(LOGIN_URL, json=LOGIN_BODY)
            self.assertEqual(
                response.status_code,
                429,
                msg=(
                    f"Expected 429 on the 6th request but got "
                    f"{response.status_code}."
                ),
            )

            # --- 429 body must be clean JSON, not a stack trace ---
            body = response.json()  # raises if body is not valid JSON
            self.assertIsInstance(
                body,
                dict,
                msg="429 response body should be a JSON object.",
            )
            # A raw exception / stack trace would contain "Traceback" text.
            body_text = response.text
            self.assertNotIn(
                "Traceback",
                body_text,
                msg="429 response body looks like a raw Python traceback.",
            )
            self.assertNotIn(
                "Exception",
                body_text,
                msg="429 response body looks like an unhandled exception.",
            )


if __name__ == "__main__":
    unittest.main()
