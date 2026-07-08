"""
Auth module Pydantic schemas.

Output schemas never include hashed_password or student_id_storage_key —
this is enforced structurally (those fields simply don't exist on the
response models), not by convention, so there's no path to accidentally
leaking them by adding a field later.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.auth.models import UserRole, UserStatus


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    school_id: uuid.UUID

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class EmailVerificationRequest(BaseModel):
    token: str


class StudentIdSubmissionResponse(BaseModel):
    message: str
    status: UserStatus


class UserPublicResponse(BaseModel):
    """Safe-to-return user representation. No password hash, no student ID."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    school_id: uuid.UUID | None
    created_at: datetime
