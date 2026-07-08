import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply
from app.shared.repository import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Review, session)

    def _with_relations(self):
        return select(Review).options(
            selectinload(Review.photos),
            selectinload(Review.reply),
        )

    async def get_by_id_with_relations(self, review_id: uuid.UUID) -> Review | None:
        result = await self.session.execute(
            self._with_relations().where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_existing(self, *, business_id: uuid.UUID, reviewer_id: uuid.UUID) -> Review | None:
        result = await self.session.execute(
            select(Review).where(
                Review.business_id == business_id,
                Review.reviewer_id == reviewer_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_business(
        self, business_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        base = self._with_relations().where(
            Review.business_id == business_id, Review.is_flagged.is_(False)
        )
        total = (await self.session.execute(
            select(func.count()).select_from(
                select(Review).where(
                    Review.business_id == business_id, Review.is_flagged.is_(False)
                ).subquery()
            )
        )).scalar_one()
        result = await self.session.execute(
            base.order_by(Review.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_average_rating(self, business_id: uuid.UUID) -> tuple[float, int]:
        result = await self.session.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.business_id == business_id, Review.is_flagged.is_(False)
            )
        )
        avg, count = result.one()
        return (round(float(avg), 2) if avg else 0.0), (count or 0)


class ReviewPhotoRepository(BaseRepository[ReviewPhoto]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ReviewPhoto, session)


class ReviewReplyRepository(BaseRepository[ReviewReply]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ReviewReply, session)
