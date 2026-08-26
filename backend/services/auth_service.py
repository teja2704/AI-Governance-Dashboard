import os
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.database.models import User


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )




def get_user_by_email(
    db: Session,
    email: str
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def create_user(
    db: Session,
    first_name: str,
    last_name: str,
    email: str,
    password: str
) -> User:
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> User | None:
    user = get_user_by_email(db, email)

    if not user or not user.is_active:
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to issue or validate tokens."
        )

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be at least 32 bytes long."
        )

    return secret


def _jwt_algorithm() -> str:
    return os.getenv(
        "JWT_ALGORITHM",
        "HS256"
    )


def _access_token_minutes() -> int:
    return int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "30"
        )
    )


def create_access_token(email: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=_access_token_minutes()
    )

    payload = {
        "sub": email,
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=_jwt_algorithm()
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[_jwt_algorithm()]
        )
    except (InvalidTokenError, RuntimeError):
        return None

    if payload.get("purpose") == "password_reset":
        return None

    subject = payload.get("sub")

    if not isinstance(subject, str):
        return None

    return subject


def ensure_bootstrap_user(db: Session) -> User | None:
    email = os.getenv("AUTH_BOOTSTRAP_USERNAME")
    password = os.getenv("AUTH_BOOTSTRAP_PASSWORD")

    if not email or not password:
        return None

    existing_user = get_user_by_email(
        db,
        email
    )

    if existing_user:
        return existing_user

    return create_user(
        db,
        "Admin",
        "User",
        email,
        password
    )


import secrets
import string
import requests
import logging

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    """Generate a 6-digit numeric OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


def send_otp_email(email: str, otp: str) -> None:
    """Send OTP via Resend API using standard requests."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error(f"RESEND_API_KEY not set. Cannot send email to {email}")
        return

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "onboarding@resend.dev",
        "to": [email],
        "subject": "Password Reset Code",
        "html": f"<p>Your reset code is <strong>{otp}</strong>, expires in 10 minutes.</p>"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        res_data = response.json()
        email_id = res_data.get("id", "unknown")
        logger.info(f"Successfully sent reset email to {email} (Resend ID: {email_id})")
    except requests.RequestException as e:
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_details += f" | Body: {e.response.text}"
        logger.error(f"Failed to send reset email to {email}. Error: {error_details}")


def create_reset_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "purpose": "password_reset",
        "exp": expires_at
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def decode_reset_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[_jwt_algorithm()]
        )
    except (InvalidTokenError, RuntimeError):
        return None

    if payload.get("purpose") != "password_reset":
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None

    try:
        return int(subject)
    except ValueError:
        return None


def verify_google_token(id_token: str) -> dict | None:
    """Verifies a Google ID token and returns the payload if valid."""
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def get_or_create_google_user(db: Session, google_info: dict) -> User | None:
    """Finds a user by email, links their google_id, or creates a new one."""
    email = google_info.get("email")
    google_id = google_info.get("sub")
    
    if not email or not google_id:
        return None

    first_name = google_info.get("given_name", "Unknown")
    last_name = google_info.get("family_name", "Unknown")
    avatar_url = google_info.get("picture")

    user = get_user_by_email(db, email)
    if user:
        if not user.google_id:
            user.google_id = google_id
            if avatar_url:
                user.avatar_url = avatar_url
            db.commit()
            db.refresh(user)
        return user
    
    # Create new user via Google
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        google_id=google_id,
        avatar_url=avatar_url,
        hashed_password=hash_password(secrets.token_urlsafe(32))
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

