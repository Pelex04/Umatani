"""
Auth module routes.

Rate limiting is applied per-route at the stricter RATE_LIMIT_AUTH bound
(default 5/minute) on credential-guessing-relevant endpoints (login,
register, refresh) to blunt brute-force and enumeration attempts, layered
on top of the account-lockout mechanism in the service layer.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    EmailVerificationRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    StudentIdSubmissionResponse,
    TokenPairResponse,
    UserLoginRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.modules.auth.service import AuthError, AuthService

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublicResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def register(
    request: Request,
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserPublicResponse:
    service = AuthService(db)
    try:
        user, verification_token = await service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            school_id=payload.school_id,
        )
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    from app.core.email import send_verification_email
    await send_verification_email(
        to=user.email, full_name=user.full_name, token=verification_token
    )
    return UserPublicResponse.model_validate(user)


@router.post("/verify-email", response_model=UserPublicResponse)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def verify_email(
    request: Request,
    payload: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> UserPublicResponse:
    service = AuthService(db)
    try:
        user = await service.verify_email(payload.token)
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return UserPublicResponse.model_validate(user)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Always returns 204 regardless of whether the email matched an account —
    same information-disclosure precaution as register()'s generic error —
    so this can't be used to enumerate which emails are registered.
    """
    service = AuthService(db)
    result = await service.resend_verification_email(payload.email)
    await db.commit()
    if result is not None:
        user, verification_token = result
        from app.core.email import send_verification_email
        await send_verification_email(
            to=user.email, full_name=user.full_name, token=verification_token
        )


@router.post("/login", response_model=TokenPairResponse)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def login(
    request: Request,
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPairResponse:
    service = AuthService(db)
    try:
        _user, access_token, refresh_token = await service.login(
            email=payload.email, password=payload.password
        )
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPairResponse:
    service = AuthService(db)
    try:
        access_token, refresh_token = await service.refresh(payload.refresh_token)
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    await db.commit()


@router.get("/me", response_model=UserPublicResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserPublicResponse:
    return UserPublicResponse.model_validate(user)


@router.post("/student-id", response_model=StudentIdSubmissionResponse)
async def submit_student_id(
    storage_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudentIdSubmissionResponse:
    """
    Accepts a storage key referencing an already-uploaded student ID image
    (uploaded via the media module's signed-upload flow, not inline here —
    keeping upload validation/MIME checks in one place). This endpoint
    only records the association and transitions account status.
    """
    service = AuthService(db)
    try:
        updated_user = await service.submit_student_id(user, storage_key)
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return StudentIdSubmissionResponse(
        message="Student ID submitted. Your account is now pending admin review.",
        status=updated_user.status,
    )
