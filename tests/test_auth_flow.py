import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

from backend.database.db import SessionLocal
from backend.database.models import User, PasswordReset
from backend.main import app
from backend.services.auth_service import verify_password

class AuthFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    @classmethod
    def tearDownClass(cls):
        from backend.database.db import engine
        engine.dispose()
        TEST_DB_PATH.unlink(missing_ok=True)

    def test_signup_success(self):
        with TestClient(app) as client:
            response = client.post(
                "/auth/signup",
                json={
                    "first_name": "New",
                    "last_name": "User",
                    "email": "newuser@example.com",
                    "password": "StrongPassword123!"
                }
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("access_token", response.json())


    def test_signup_duplicate_email(self):
        with TestClient(app) as client:
            client.post(
                "/auth/signup",
                json={
                    "first_name": "Dup",
                    "last_name": "Email1",
                    "email": "dupemail@example.com",
                    "password": "StrongPassword123!"
                }
            )
            response = client.post(
                "/auth/signup",
                json={
                    "first_name": "Dup",
                    "last_name": "Email2",
                    "email": "dupemail@example.com",
                    "password": "StrongPassword123!"
                }
            )
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["detail"], "Email already taken.")
            
    def test_forgot_password_always_returns_200(self):
        with TestClient(app) as client:
            response = client.post(
                "/auth/forgot-password",
                json={"email": "nonexistent@example.com"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["message"], "If this email exists, a code has been sent.")

    def test_full_reset_password_flow(self):
        with TestClient(app) as client:
            # 1. Signup user
            client.post(
                "/auth/signup",
                json={
                    "first_name": "Reset",
                    "last_name": "User",
                    "email": "resetuser@example.com",
                    "password": "OldPassword123!"
                }
            )
            
            # 2. Forgot Password
            with patch("backend.routes.auth_routes.send_otp_email") as mock_send_email:
                response = client.post(
                    "/auth/forgot-password",
                    json={"email": "resetuser@example.com"}
                )
                self.assertEqual(response.status_code, 200)
                mock_send_email.assert_called_once()
            
            # Extract OTP from DB since mock swallowed it
            db = SessionLocal()
            reset_record = db.query(PasswordReset).filter(PasswordReset.used == False).order_by(PasswordReset.created_at.desc()).first()
            otp = reset_record.otp_code
            db.close()
            
            # 3. Verify OTP
            verify_response = client.post(
                "/auth/verify-otp",
                json={"email": "resetuser@example.com", "otp": otp}
            )
            self.assertEqual(verify_response.status_code, 200)
            reset_token = verify_response.json()["reset_token"]
            
            # 4. Reset Password
            reset_response = client.post(
                "/auth/reset-password",
                json={"reset_token": reset_token, "new_password": "NewPassword123!"}
            )
            self.assertEqual(reset_response.status_code, 200)
            
            # Verify password was updated
            db = SessionLocal()
            user = db.query(User).filter(User.email == "resetuser@example.com").first()
            self.assertTrue(verify_password("NewPassword123!", user.hashed_password))
            db.close()
            
    def test_verify_otp_invalid(self):
        with TestClient(app) as client:
            response = client.post(
                "/auth/verify-otp",
                json={"email": "admin@example.com", "otp": "000000"}
            )
            self.assertEqual(response.status_code, 400)

    def test_reset_password_invalid_token(self):
        with TestClient(app) as client:
            response = client.post(
                "/auth/reset-password",
                json={"reset_token": "invalid_token", "new_password": "NewPassword123!"}
            )
            self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
