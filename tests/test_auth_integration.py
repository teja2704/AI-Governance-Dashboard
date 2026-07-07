import os
import tempfile
import unittest
from pathlib import Path

db_file = tempfile.NamedTemporaryFile(
    delete=False,
    suffix=".db"
)
db_file.close()

os.environ["DATABASE_URL"] = f"sqlite:///{Path(db_file.name).as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["JWT_ALGORITHM"] = "HS256"

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.main import app


class AuthIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    @classmethod
    def tearDownClass(cls):
        from backend.database.db import engine

        engine.dispose()
        Path(db_file.name).unlink(missing_ok=True)

    def test_protected_route_requires_jwt(self):
        with TestClient(app) as client:
            response = client.get("/prompts/")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
