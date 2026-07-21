from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.rate_limiter import limiter
from backend.schemas.auth_schema import LoginRequest, TokenResponse
from backend.services.auth_service import (
    authenticate_user,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
@limiter.limit("5/minute")
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        body.username,
        body.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return TokenResponse(
        access_token=create_access_token(user.username)
    )