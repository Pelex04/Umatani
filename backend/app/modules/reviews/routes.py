import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_verified_business_owner, require_role
from app.modules.auth.models import User, UserRole
from app.modules.reviews.schemas import (
    PaginatedReviewResponse,
    ReviewAdminResponse,
    ReviewCreateRequest,
    ReviewPublicResponse,
    ReviewReplyRequest,
)
from app.modules.reviews.service import ReviewError, ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])
admin_router = APIRouter(
    prefix="/admin/reviews", tags=["admin", "reviews"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.get("", response_model=PaginatedReviewResponse)
async def list_reviews(
    business_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> PaginatedReviewResponse:
    service = ReviewService(db)
    try:
        items, total = await service.list_for_business(business_id, offset=offset, limit=limit)
    except ReviewError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return PaginatedReviewResponse(
        total=total, offset=offset, limit=limit,
        items=[ReviewPublicResponse.model_validate(r) for r in items],
    )


@router.post("", response_model=ReviewPublicResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewPublicResponse:
    service = ReviewService(db)
    try:
        review = await service.create(
            reviewer=user,
            business_id=payload.business_id,
            rating=payload.rating,
            comment=payload.comment,
            service_received=payload.service_received,
            photo_storage_keys=payload.photo_storage_keys,
        )
        await db.commit()
    except ReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return ReviewPublicResponse.model_validate(review)


@router.post("/{review_id}/reply", response_model=ReviewPublicResponse)
async def add_reply(
    review_id: uuid.UUID,
    payload: ReviewReplyRequest,
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> ReviewPublicResponse:
    service = ReviewService(db)
    try:
        review = await service.add_reply(owner=owner, review_id=review_id, content=payload.content)
        await db.commit()
    except ReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return ReviewPublicResponse.model_validate(review)


@admin_router.patch("/{review_id}/flag", response_model=ReviewAdminResponse)
async def flag_review(
    review_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ReviewAdminResponse:
    service = ReviewService(db)
    try:
        review = await service.flag(admin=admin, review_id=review_id)
        await db.commit()
    except ReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ReviewAdminResponse.model_validate(review)


@admin_router.patch("/{review_id}/unflag", response_model=ReviewAdminResponse)
async def unflag_review(
    review_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ReviewAdminResponse:
    service = ReviewService(db)
    try:
        review = await service.unflag(admin=admin, review_id=review_id)
        await db.commit()
    except ReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ReviewAdminResponse.model_validate(review)


@admin_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ReviewService(db)
    try:
        await service.delete(admin=admin, review_id=review_id)
        await db.commit()
    except ReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
