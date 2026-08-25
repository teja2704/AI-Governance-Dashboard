from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class ResetTokenResponse(BaseModel):
    reset_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
