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


def get_user_by_username(
    db: Session,
    username: str
) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


def create_user(
    db: Session,
    username: str,
    password: str
) -> User:
    user = User(
        username=username,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> User | None:
    user = get_user_by_username(db, username)

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


def create_access_token(username: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=_access_token_minutes()
    )

    payload = {
        "sub": username,
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

    subject = payload.get("sub")

    if not isinstance(subject, str):
        return None

    return subject


def ensure_bootstrap_user(db: Session) -> User | None:
    username = os.getenv("AUTH_BOOTSTRAP_USERNAME")
    password = os.getenv("AUTH_BOOTSTRAP_PASSWORD")

    if not username or not password:
        return None

    existing_user = get_user_by_username(
        db,
        username
    )

    if existing_user:
        return existing_user

    return create_user(
        db,
        username,
        password
    )
