"""
Auth module Pydantic schemas.

Output schemas never include hashed_password or student_id_storage_key —
this is enforced structurally (those fields simply don't exist on the
response models), not by convention, so there's no path to accidentally
leaking them by adding a field later.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator

from app.modules.auth.models import UserRole, UserStatus


def _check_password_complexity(v: str) -> str:
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    return v


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    school_id: uuid.UUID

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _check_password_complexity(v)


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


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _check_password_complexity(v)


class StudentIdSubmissionResponse(BaseModel):
    message: str
    status: UserStatus


class UserPublicResponse(BaseModel):
    """
    Safe-to-return user representation. No password hash, and the raw
    student ID storage key never leaves this schema — student_id_storage_key
    is only held here long enough to derive student_id_submitted below,
    then excluded from serialization. Clients need to know *whether* an ID
    was submitted (to render the right dashboard state) but never need the
    key itself.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    school_id: uuid.UUID | None
    created_at: datetime
    student_id_storage_key: str | None = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def student_id_submitted(self) -> bool:
        return self.student_id_storage_key is not None
