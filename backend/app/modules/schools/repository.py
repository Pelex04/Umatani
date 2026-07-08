from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schools.models import School, SchoolStatus
from app.shared.repository import BaseRepository


class SchoolRepository(BaseRepository[School]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(School, session)

    async def get_by_domain(self, email_domain: str) -> School | None:
        stmt = select(School).where(School.email_domain == email_domain.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_public(
        self, *, offset: int = 0, limit: int = 50, search: str | None = None
    ) -> list[School]:
        """Schools visible to visitors: approved and active only."""
        stmt = select(School).where(
            School.status == SchoolStatus.APPROVED, School.is_active.is_(True)
        )
        if search:
            stmt = stmt.where(School.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(School.name).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
