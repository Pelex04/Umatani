import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import EmailVerificationToken, RefreshToken, User
from app.shared.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
        )
        result = await self.session.execute(stmt)
        for token in result.scalars().all():
            token.revoked = True
        await self.session.flush()


class EmailVerificationTokenRepository(BaseRepository[EmailVerificationToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EmailVerificationToken, session)

    async def get_active_tokens_for_user(self, user_id: uuid.UUID) -> list[EmailVerificationToken]:
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
