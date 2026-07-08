"""
Authentication & RBAC dependencies.

`get_current_user` validates the bearer access token and loads the user.
`require_role` is a dependency factory producing role-gated dependencies,
e.g. `Depends(require_role(UserRole.ADMIN))`.

These are deliberately kept in `core`, not `modules/auth`, because every
other module depends on them — putting them in a feature module would
create a circular/upward dependency that breaks the modular-monolith
boundary described in the architecture.
"""
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.modules.auth.models import User, UserRole, UserStatus

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise unauthorized from exc

    user = await db.get(User, user_id)
    if user is None:
        raise unauthorized

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been suspended",
        )

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory: restricts a route to one or more roles."""

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return dependency


async def get_verified_business_owner(
    user: User = Depends(get_current_user),
) -> User:
    """Convenience dependency: business-owner routes that require verification."""
    if user.role != UserRole.BUSINESS_OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only business owners can perform this action",
        )
    if user.status != UserStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account must be verified before performing this action",
        )
    return user
