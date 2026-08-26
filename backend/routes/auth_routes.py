from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.rate_limiter import limiter
from backend.schemas.auth_schema import (
    LoginRequest, 
    TokenResponse, 
    SignupRequest,
    ForgotPasswordRequest,
    VerifyOtpRequest,
    ResetTokenResponse,
    ResetPasswordRequest,
    GoogleLoginRequest
)
from backend.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
    generate_otp,
    send_otp_email,
    create_reset_token,
    decode_reset_token,
    hash_password,
    verify_google_token,
    get_or_create_google_user
)
from backend.database.models import PasswordReset, User
from datetime import datetime, UTC

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
        body.email,
        body.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return TokenResponse(
        access_token=create_access_token(user.email)
    )


@router.post(
    "/signup",
    response_model=TokenResponse
)
def signup(
    body: SignupRequest,
    db: Session = Depends(get_db)
):
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long."
        )

    if get_user_by_email(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already taken."
        )

    user = create_user(db, body.first_name, body.last_name, body.email, body.password)
    return TokenResponse(
        access_token=create_access_token(user.email)
    )

@router.post(
    "/google",
    response_model=TokenResponse
)
def google_login(
    body: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    google_info = verify_google_token(body.id_token)
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
        
    user = get_or_create_google_user(db, google_info)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not create user"
        )
        
    return TokenResponse(
        access_token=create_access_token(user.email)
    )


@router.post(
    "/forgot-password"
)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, body.email)
    
    # Always return 200, even if user is not found, to prevent email enumeration
    success_msg = {"message": "If this email exists, a code has been sent."}
    
    if not user:
        return success_msg
        
    otp = generate_otp()
    from datetime import timedelta
    expires_at = datetime.now(UTC) + timedelta(minutes=10)
    
    reset_record = PasswordReset(
        user_id=user.id,
        otp_code=otp,
        expires_at=expires_at
    )
    db.add(reset_record)
    db.commit()
    
    send_otp_email(user.email, otp)
    
    return success_msg


@router.post(
    "/verify-otp",
    response_model=ResetTokenResponse
)
def verify_otp(
    body: VerifyOtpRequest,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, body.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
        
    reset_record = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user.id,
            PasswordReset.used == False,
            PasswordReset.expires_at > datetime.now(UTC)
        )
        .order_by(PasswordReset.created_at.desc())
        .first()
    )
    
    if not reset_record or reset_record.otp_code != body.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
        
    reset_record.used = True
    db.commit()
    
    return ResetTokenResponse(
        reset_token=create_reset_token(user.id)
    )


@router.post(
    "/reset-password"
)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    user_id = decode_reset_token(body.reset_token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long."
        )
        
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    
    return {"message": "Password reset successful"}