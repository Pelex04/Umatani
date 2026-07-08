"""
Reviews service.

Key business rules:
1. Only authenticated users may submit reviews (spec requirement).
2. Business owners cannot review their own business (anti-gaming).
3. One review per user per business — attempting a second raises an error.
4. The business must be approved — you cannot review a pending/suspended profile.
5. Photo storage keys are ownership-verified (same pattern as student ID / logo).
6. After any create/flag operation, average_rating and review_count on
   the Business row are recomputed and updated atomically in the same
   transaction. No eventual consistency, no background job needed at V1 scale.
7. Only the business owner may reply to a review on their own business.
   Only one reply per review (unique constraint enforced at DB level too).
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.businesses.models import Business, BusinessStatus
from app.modules.media.service import MediaService
from app.modules.media.validation import UploadPurpose
from app.modules.reviews.models import Review, ReviewPhoto, ReviewReply
from app.modules.reviews.repository import (
    ReviewPhotoRepository,
    ReviewReplyRepository,
    ReviewRepository,
)
from app.shared.audit_service import record_audit_event


class ReviewError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.reviews = ReviewRepository(db)
        self.photos = ReviewPhotoRepository(db)
        self.replies = ReviewReplyRepository(db)

    async def _get_approved_business(self, business_id: uuid.UUID) -> Business:
        biz = await self.db.get(Business, business_id)
        if biz is None or biz.status != BusinessStatus.APPROVED:
            raise ReviewError("Business not found")
        return biz

    async def _update_business_rating(self, business_id: uuid.UUID) -> None:
        avg, count = await self.reviews.get_average_rating(business_id)
        await self.db.execute(
            update(Business)
            .where(Business.id == business_id)
            .values(average_rating=avg, review_count=count)
        )

    async def create(
        self,
        *,
        reviewer: User,
        business_id: uuid.UUID,
        rating: int,
        comment: str,
        service_received: str | None,
        photo_storage_keys: list[str],
    ) -> Review:
        biz = await self._get_approved_business(business_id)

        if biz.owner_id == reviewer.id:
            raise ReviewError("You cannot review your own business")

        existing = await self.reviews.get_existing(
            business_id=business_id, reviewer_id=reviewer.id
        )
        if existing is not None:
            raise ReviewError("You have already reviewed this business")

        for key in photo_storage_keys:
            if not MediaService.verify_key_ownership(
                key, expected_purpose=UploadPurpose.REVIEW_PHOTO, expected_owner_id=reviewer.id
            ):
                raise ReviewError("Invalid storage key for review photo")

        review = await self.reviews.create(
            business_id=business_id,
            reviewer_id=reviewer.id,
            rating=rating,
            comment=comment,
            service_received=service_received,
        )

        for key in photo_storage_keys:
            self.db.add(ReviewPhoto(review_id=review.id, storage_key=key))
        await self.db.flush()

        await self._update_business_rating(business_id)

        await record_audit_event(
            self.db, action="review.created", resource_type="review",
            resource_id=str(review.id), actor_id=reviewer.id, actor_role=reviewer.role,
        )
        return await self.reviews.get_by_id_with_relations(review.id)

    async def list_for_business(
        self, business_id: uuid.UUID, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        await self._get_approved_business(business_id)
        return await self.reviews.list_for_business(business_id, offset=offset, limit=limit)

    async def add_reply(self, *, owner: User, review_id: uuid.UUID, content: str) -> Review:
        review = await self.reviews.get_by_id_with_relations(review_id)
        if review is None:
            raise ReviewError("Review not found")

        biz = await self.db.get(Business, review.business_id)
        if biz is None or biz.owner_id != owner.id:
            raise ReviewError("You can only reply to reviews on your own business")

        if review.reply is not None:
            raise ReviewError("You have already replied to this review")

        self.db.add(ReviewReply(review_id=review.id, content=content))
        await self.db.flush()

        await record_audit_event(
            self.db, action="review.reply_added", resource_type="review",
            resource_id=str(review.id), actor_id=owner.id, actor_role=owner.role,
        )
        # Force fresh load of reply relation after insert
        await self.db.refresh(review)
        # Re-load relations after scalar refresh
        await self.db.refresh(review, attribute_names=["photos", "reply"])
        return review

    async def flag(self, *, admin: User, review_id: uuid.UUID) -> Review:
        review = await self.reviews.get_by_id_with_relations(review_id)
        if review is None:
            raise ReviewError("Review not found")
        review.is_flagged = True
        await self.db.flush()
        await self._update_business_rating(review.business_id)
        await record_audit_event(
            self.db, action="review.flagged", resource_type="review",
            resource_id=str(review.id), actor_id=admin.id, actor_role=admin.role,
        )
        await self.db.refresh(review)
        # Re-load relations after scalar refresh
        await self.db.refresh(review, attribute_names=["photos", "reply"])
        return review

    async def unflag(self, *, admin: User, review_id: uuid.UUID) -> Review:
        review = await self.reviews.get_by_id_with_relations(review_id)
        if review is None:
            raise ReviewError("Review not found")
        review.is_flagged = False
        await self.db.flush()
        await self._update_business_rating(review.business_id)
        await self.db.refresh(review)
        # Re-load relations after scalar refresh
        await self.db.refresh(review, attribute_names=["photos", "reply"])
        return review

    async def delete(self, *, admin: User, review_id: uuid.UUID) -> None:
        review = await self.reviews.get_by_id_with_relations(review_id)
        if review is None:
            raise ReviewError("Review not found")
        business_id = review.business_id
        await self.reviews.delete(review)
        await self._update_business_rating(business_id)
        await record_audit_event(
            self.db, action="review.deleted", resource_type="review",
            resource_id=str(review_id), actor_id=admin.id, actor_role=admin.role,
        )
