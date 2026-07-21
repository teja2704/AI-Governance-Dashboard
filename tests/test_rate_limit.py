import os
import tempfile
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment must be set before any backend module is imported so that
# init_db() and the ORM engine pick up the correct SQLite URL.
# ---------------------------------------------------------------------------
db_file = tempfile.NamedTemporaryFile(
    delete=False,
    suffix=".db"
)
db_file.close()

os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["AUTH_BOOTSTRAP_USERNAME"] = "admin@example.com"
os.environ["AUTH_BOOTSTRAP_PASSWORD"] = "AdminPassword123!"

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.main import app
from backend.rate_limiter import limiter


LOGIN_URL = "/auth/login"
LOGIN_BODY = {
    "username": os.environ["AUTH_BOOTSTRAP_USERNAME"],
    "password": os.environ["AUTH_BOOTSTRAP_PASSWORD"],
}


class RateLimitTest(unittest.TestCase):
    """Verifies that /auth/login enforces a 5-requests-per-minute limit."""

    @classmethod
    def setUpClass(cls):
        import backend.database.db as db_module
        import backend.database.init_db as init_db_module
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        os.environ["DATABASE_URL"] = f"sqlite:///{Path(db_file.name).as_posix()}"

        db_module.engine.dispose()

        database_url = os.environ["DATABASE_URL"]
        engine_kwargs = {}
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if database_url in {"sqlite://", "sqlite:///:memory:"}:
                engine_kwargs["poolclass"] = StaticPool

        db_module.engine = create_engine(database_url, **engine_kwargs)
        db_module.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=db_module.engine,
        )
        init_db_module.engine = db_module.engine
        init_db_module.SessionLocal = db_module.SessionLocal

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        limiter._storage.reset()

    @classmethod
    def tearDownClass(cls):
        from backend.database.db import engine

        engine.dispose()
        Path(db_file.name).unlink(missing_ok=True)

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
