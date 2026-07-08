import uuid
from collections.abc import Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.businesses.models import Business, BusinessStatus, PortfolioItem, Service
from app.shared.repository import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Business, session)

    def _with_relations(self):
        """Eager-load services and portfolio items in a single query."""
        return (
            select(Business)
            .options(
                selectinload(Business.services),
                selectinload(Business.portfolio_items),
            )
        )

    async def get_by_id_with_relations(self, business_id: uuid.UUID) -> Business | None:
        result = await self.session.execute(
            self._with_relations().where(Business.id == business_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Business | None:
        result = await self.session.execute(
            self._with_relations().where(Business.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: uuid.UUID) -> Business | None:
        result = await self.session.execute(
            self._with_relations().where(Business.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        keyword: str | None = None,
        category_id: uuid.UUID | None = None,
        school_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        status: BusinessStatus = BusinessStatus.APPROVED,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Business], int]:
        """
        Returns (items, total_count) for paginated search.
        Lightweight query — does NOT eager-load relations, returns
        BusinessListItemResponse-compatible rows only.
        """
        stmt = select(Business).where(Business.status == status)

        if keyword:
            stmt = stmt.where(
                or_(
                    Business.name.ilike(f"%{keyword}%"),
                    Business.description.ilike(f"%{keyword}%"),
                )
            )
        if category_id:
            stmt = stmt.where(Business.category_id == category_id)
        if school_id:
            stmt = stmt.where(Business.school_id == school_id)
        if min_rating is not None:
            stmt = stmt.where(Business.average_rating >= min_rating)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Business.average_rating.desc(), Business.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Service, session)

    async def replace_for_business(
        self, business_id: uuid.UUID, services_data: list[dict]
    ) -> None:
        existing = await self.session.execute(
            select(Service).where(Service.business_id == business_id)
        )
        for svc in existing.scalars().all():
            await self.session.delete(svc)
        await self.session.flush()
        for data in services_data:
            self.session.add(Service(business_id=business_id, **data))
        await self.session.flush()


class PortfolioItemRepository(BaseRepository[PortfolioItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PortfolioItem, session)

    async def get_for_business(self, business_id: uuid.UUID) -> list[PortfolioItem]:
        result = await self.session.execute(
            select(PortfolioItem)
            .where(PortfolioItem.business_id == business_id)
            .order_by(PortfolioItem.display_order)
        )
        return list(result.scalars().all())
