"""
Businesses routes.

URL design:
  GET  /businesses              - visitor search/browse (no auth)
  GET  /businesses/{id}         - visitor profile view (no auth)
  GET  /businesses/slug/{slug}  - visitor profile view by slug (no auth)
  POST /businesses              - owner creates their business
  GET  /businesses/me           - owner views their own business
  PATCH /businesses/me          - owner updates profile
  PATCH /businesses/me/logo     - owner sets logo
  PATCH /businesses/me/cover    - owner sets cover image
  POST /businesses/me/portfolio - owner adds portfolio item
  DELETE /businesses/me/portfolio/{item_id} - owner removes item

  GET    /admin/businesses            - admin lists (all statuses)
  GET    /admin/businesses/{id}       - admin views any business
  PATCH  /admin/businesses/{id}/approve
  PATCH  /admin/businesses/{id}/suspend
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_verified_business_owner, require_role
from app.modules.auth.models import User, UserRole
from app.modules.businesses.models import BusinessStatus, PortfolioItemType
from app.modules.businesses.schemas import (
    BusinessAdminResponse,
    BusinessCreateRequest,
    BusinessListItemResponse,
    BusinessOwnerResponse,
    BusinessPublicResponse,
    BusinessUpdateRequest,
    PortfolioItemAddRequest,
    PortfolioItemResponse,
)
from app.modules.businesses.service import BusinessError, BusinessService

router = APIRouter(prefix="/businesses", tags=["businesses"])
admin_router = APIRouter(
    prefix="/admin/businesses",
    tags=["admin", "businesses"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


class PaginatedBusinessResponse(dict):
    pass


@router.get("", response_model=dict)
async def search_businesses(
    keyword: str | None = Query(default=None, max_length=255),
    category_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    min_rating: float | None = Query(default=None, ge=0.0, le=5.0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = BusinessService(db)
    items, total = await service.search(
        keyword=keyword,
        category_id=category_id,
        school_id=school_id,
        min_rating=min_rating,
        offset=offset,
        limit=limit,
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [BusinessListItemResponse.model_validate(b) for b in items],
    }


@router.get("/me", response_model=BusinessOwnerResponse)
async def get_own_business(
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> BusinessOwnerResponse:
    service = BusinessService(db)
    try:
        biz = await service.get_own(owner)
    except BusinessError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return BusinessOwnerResponse.model_validate(biz)


@router.get("/slug/{slug}", response_model=BusinessPublicResponse)
async def get_business_by_slug(
    slug: str, db: AsyncSession = Depends(get_db)
) -> BusinessPublicResponse:
    service = BusinessService(db)
    try:
        biz = await service.get_public_by_slug(slug)
    except BusinessError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return BusinessPublicResponse.model_validate(biz)


@router.get("/{business_id}", response_model=BusinessPublicResponse)
async def get_business(
    business_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> BusinessPublicResponse:
    service = BusinessService(db)
    try:
        biz = await service.get_public(business_id)
    except BusinessError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return BusinessPublicResponse.model_validate(biz)


@router.post("", response_model=BusinessOwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    payload: BusinessCreateRequest,
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> BusinessOwnerResponse:
    service = BusinessService(db)
    services_data = [
        {
            "name": s.name,
            "description": s.description,
            "price_range": s.price_range,
            "display_order": s.display_order,
        }
        for s in payload.services
    ]
    contact_fields = {
        "whatsapp": payload.whatsapp,
        "phone": payload.phone,
        "contact_email": payload.contact_email,
        "website": payload.website,
        "instagram": payload.instagram,
        "twitter": payload.twitter,
        "facebook": payload.facebook,
        "tiktok": payload.tiktok,
    }
    try:
        biz = await service.create(
            owner=owner,
            name=payload.name,
            description=payload.description,
            category_id=payload.category_id,
            services_data=services_data,
            **contact_fields,
        )
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return BusinessOwnerResponse.model_validate(biz)


@router.patch("/me", response_model=BusinessOwnerResponse)
async def update_business(
    payload: BusinessUpdateRequest,
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> BusinessOwnerResponse:
    service = BusinessService(db)
    updates = payload.model_dump(exclude_none=True, exclude={"services"})
    services_data = (
        [
            {
                "name": s.name,
                "description": s.description,
                "price_range": s.price_range,
                "display_order": s.display_order,
            }
            for s in payload.services
        ]
        if payload.services is not None
        else None
    )
    try:
        biz = await service.update(owner=owner, updates=updates, services_data=services_data)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        # "no business profile" is a 404; other domain errors are 400
        http_status = (
            status.HTTP_404_NOT_FOUND
            if "do not have" in exc.message
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=http_status, detail=exc.message) from exc
    return BusinessOwnerResponse.model_validate(biz)


@router.patch("/me/logo", response_model=BusinessOwnerResponse)
async def update_logo(
    storage_key: str = Query(..., min_length=1, max_length=512),
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> BusinessOwnerResponse:
    service = BusinessService(db)
    try:
        biz = await service.update_logo(owner=owner, storage_key=storage_key)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return BusinessOwnerResponse.model_validate(biz)


@router.patch("/me/cover", response_model=BusinessOwnerResponse)
async def update_cover(
    storage_key: str = Query(..., min_length=1, max_length=512),
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> BusinessOwnerResponse:
    service = BusinessService(db)
    try:
        biz = await service.update_cover(owner=owner, storage_key=storage_key)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return BusinessOwnerResponse.model_validate(biz)


@router.post("/me/portfolio", response_model=PortfolioItemResponse, status_code=status.HTTP_201_CREATED)
async def add_portfolio_item(
    payload: PortfolioItemAddRequest,
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> PortfolioItemResponse:
    service = BusinessService(db)
    try:
        item = await service.add_portfolio_item(
            owner=owner,
            item_type=payload.item_type,
            storage_key_or_url=payload.storage_key_or_url,
            caption=payload.caption,
            display_order=payload.display_order,
        )
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return PortfolioItemResponse.model_validate(item)


@router.delete("/me/portfolio/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_portfolio_item(
    item_id: uuid.UUID,
    owner: User = Depends(get_verified_business_owner),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = BusinessService(db)
    try:
        await service.remove_portfolio_item(owner=owner, item_id=item_id)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ------------------------------------------------------------------ #
# Admin routes                                                         #
# ------------------------------------------------------------------ #

@admin_router.get("", response_model=dict)
async def admin_list_businesses(
    status_filter: BusinessStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = BusinessService(db)
    items, total = await service.admin_list(
        status=status_filter, offset=offset, limit=limit
    )
    # Admin list uses the lightweight card response (no relations) for
    # performance — the full detail view at /{business_id} loads relations.
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [BusinessListItemResponse.model_validate(b) for b in items],
    }


@admin_router.get("/{business_id}", response_model=BusinessAdminResponse)
async def admin_get_business(
    business_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> BusinessAdminResponse:
    service = BusinessService(db)
    try:
        biz = await service.admin_get(business_id)
    except BusinessError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return BusinessAdminResponse.model_validate(biz)


@admin_router.patch("/{business_id}/approve", response_model=BusinessAdminResponse)
async def admin_approve_business(
    business_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BusinessAdminResponse:
    service = BusinessService(db)
    try:
        biz = await service.approve(admin=admin, business_id=business_id)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return BusinessAdminResponse.model_validate(biz)


@admin_router.patch("/{business_id}/suspend", response_model=BusinessAdminResponse)
async def admin_suspend_business(
    business_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BusinessAdminResponse:
    service = BusinessService(db)
    try:
        biz = await service.suspend(admin=admin, business_id=business_id)
        await db.commit()
    except BusinessError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return BusinessAdminResponse.model_validate(biz)
