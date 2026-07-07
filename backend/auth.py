from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import User
from backend.services.auth_service import (
    decode_access_token,
    get_user_by_username
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token.",
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise _unauthorized()

    username = decode_access_token(
        credentials.credentials
    )

    if username is None:
        raise _unauthorized()

    user = get_user_by_username(
        db,
        username
    )

    if user is None or not user.is_active:
        raise _unauthorized()

    return user
