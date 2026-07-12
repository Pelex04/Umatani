import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.auth.models import User, UserRole
from app.modules.categories.schemas import (
    CategoryAdminResponse,
    CategoryCreateRequest,
    CategoryPublicResponse,
    CategoryUpdateRequest,
)
from app.modules.categories.service import CategoryError, CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])
admin_router = APIRouter(
    prefix="/admin/categories",
    tags=["admin", "categories"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.get("", response_model=list[CategoryPublicResponse])
async def list_categories(
    response: Response, db: AsyncSession = Depends(get_db)
) -> list[CategoryPublicResponse]:
    # Categories change maybe a handful of times ever (admin-managed).
    # Beyond the frontend's own in-session cache, this lets browsers and
    # any CDN in front of the API skip the round trip entirely for repeat
    # visits within the window — stale-while-revalidate means a slightly
    # out-of-date list serves instantly while a fresh one loads in the
    # background, rather than blocking on it.
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"
    service = CategoryService(db)
    cats = await service.list_public()
    return [CategoryPublicResponse.model_validate(c) for c in cats]


@router.get("/{category_id}", response_model=CategoryPublicResponse)
async def get_category(
    category_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> CategoryPublicResponse:
    service = CategoryService(db)
    try:
        cat = await service.get_public(category_id)
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return CategoryPublicResponse.model_validate(cat)


@admin_router.get("", response_model=list[CategoryAdminResponse])
async def admin_list_categories(
    db: AsyncSession = Depends(get_db),
) -> list[CategoryAdminResponse]:
    service = CategoryService(db)
    cats = await service.list_admin()
    return [CategoryAdminResponse.model_validate(c) for c in cats]


@admin_router.post("", response_model=CategoryAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_category(
    payload: CategoryCreateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> CategoryAdminResponse:
    service = CategoryService(db)
    try:
        cat = await service.create(
            admin=admin,
            name=payload.name,
            description=payload.description,
            icon_url=payload.icon_url,
            display_order=payload.display_order,
        )
        await db.commit()
    except CategoryError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return CategoryAdminResponse.model_validate(cat)


@admin_router.patch("/{category_id}", response_model=CategoryAdminResponse)
async def admin_update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> CategoryAdminResponse:
    service = CategoryService(db)
    try:
        cat = await service.update(
            admin=admin,
            category_id=category_id,
            name=payload.name,
            description=payload.description,
            icon_url=payload.icon_url,
            display_order=payload.display_order,
            is_active=payload.is_active,
        )
        await db.commit()
    except CategoryError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return CategoryAdminResponse.model_validate(cat)
