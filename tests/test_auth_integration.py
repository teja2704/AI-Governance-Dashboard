import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

db_file = tempfile.NamedTemporaryFile(
    delete=False,
    suffix=".db"
)
db_file.close()

os.environ["DATABASE_URL"] = f"sqlite:///{Path(db_file.name).as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["AUTH_BOOTSTRAP_USERNAME"] = "admin@example.com"
os.environ["AUTH_BOOTSTRAP_PASSWORD"] = "AdminPassword123!"

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.database.db import SessionLocal
from backend.database.models import User
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

    def _auth_headers(self, client: TestClient) -> dict[str, str]:
        response = client.post(
            "/auth/login",
            json={
                "username": os.environ["AUTH_BOOTSTRAP_USERNAME"],
                "password": os.environ["AUTH_BOOTSTRAP_PASSWORD"]
            }
        )

        self.assertEqual(response.status_code, 200)

        return {
            "Authorization": f"Bearer {response.json()['access_token']}"
        }

    def _submit_generated_prompt(
        self,
        client: TestClient,
        headers: dict[str, str],
        response_text: str
    ) -> dict:
        with patch(
            "backend.routes.prompt_routes.generate_response",
            return_value=response_text
        ):
            response = client.post(
                "/prompts/generate",
                headers=headers,
                json={
                    "prompt": "Evaluate this response."
                }
            )

        self.assertEqual(response.status_code, 200)

        return response.json()

    def _current_user_id(self) -> int:
        db = SessionLocal()

        try:
            user = (
                db.query(User)
                .filter(
                    User.username ==
                    os.environ["AUTH_BOOTSTRAP_USERNAME"]
                )
                .first()
            )

            self.assertIsNotNone(user)

            return user.id
        finally:
            db.close()

    def test_prompt_submission_creates_response_and_automated_evaluation(self):
        with TestClient(app) as client:
            headers = self._auth_headers(client)
            result = self._submit_generated_prompt(
                client,
                headers,
                "This is a complete generated response."
            )

            response = client.get(
                f"/responses/{result['response_id']}",
                headers=headers
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["prompt_id"],
                result["prompt_id"]
            )

            evaluations = client.get(
                f"/evaluations/{result['response_id']}",
                headers=headers
            )

            self.assertEqual(evaluations.status_code, 200)
            self.assertEqual(len(evaluations.json()), 1)
            self.assertEqual(
                evaluations.json()[0]["evaluation_type"],
                "automated"
            )

    def test_empty_or_banned_word_response_gets_flagged(self):
        with TestClient(app) as client:
            headers = self._auth_headers(client)
            result = self._submit_generated_prompt(
                client,
                headers,
                "forbidden"
            )

            evaluations = client.get(
                f"/evaluations/{result['response_id']}",
                headers=headers
            )

            self.assertEqual(evaluations.status_code, 200)

            flags = evaluations.json()[0]["flags"]

            self.assertIn(
                "empty_or_near_empty_response",
                flags
            )
            self.assertIn(
                "banned_word:forbidden",
                flags
            )

    def test_human_evaluation_requires_auth(self):
        with TestClient(app) as client:
            response = client.post(
                "/evaluations/",
                json={
                    "response_id": 1,
                    "score": 4,
                    "notes": "Looks acceptable."
                }
            )

        self.assertEqual(response.status_code, 401)

    def test_human_evaluation_uses_jwt_user_not_request_body(self):
        with TestClient(app) as client:
            headers = self._auth_headers(client)
            result = self._submit_generated_prompt(
                client,
                headers,
                "This is another complete generated response."
            )

            response = client.post(
                "/evaluations/",
                headers=headers,
                json={
                    "response_id": result["response_id"],
                    "score": 5,
                    "notes": "Reviewed by a human.",
                    "evaluator_id": 999999
                }
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["evaluator_id"],
                self._current_user_id()
            )
            self.assertNotEqual(
                response.json()["evaluator_id"],
                999999
            )

    def test_response_evaluations_include_automated_and_human(self):
        with TestClient(app) as client:
            headers = self._auth_headers(client)
            result = self._submit_generated_prompt(
                client,
                headers,
                "A generated response for both evaluation types."
            )

            human = client.post(
                "/evaluations/",
                headers=headers,
                json={
                    "response_id": result["response_id"],
                    "score": 4,
                    "notes": "Human review is complete."
                }
            )

            self.assertEqual(human.status_code, 200)

            evaluations = client.get(
                f"/evaluations/{result['response_id']}",
                headers=headers
            )

            self.assertEqual(evaluations.status_code, 200)

            evaluation_types = {
                item["evaluation_type"]
                for item in evaluations.json()
            }

            self.assertEqual(
                evaluation_types,
                {"automated", "human"}
            )


if __name__ == "__main__":
    unittest.main()
