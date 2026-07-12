import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.auth.models import User, UserRole
from app.modules.schools.models import SchoolStatus
from app.modules.schools.schemas import (
    SchoolAdminResponse,
    SchoolCreateRequest,
    SchoolPublicResponse,
    SchoolUpdateRequest,
)
from app.modules.schools.service import SchoolError, SchoolService

router = APIRouter(prefix="/schools", tags=["schools"])
admin_router = APIRouter(
    prefix="/admin/schools",
    tags=["admin", "schools"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


# --- Public (visitor) endpoints — no authentication required ---


@router.get("", response_model=list[SchoolPublicResponse])
async def list_schools(
    response: Response,
    search: str | None = Query(default=None, max_length=255),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[SchoolPublicResponse]:
    # Same reasoning as categories: schools are admin-managed and change
    # rarely. Only cache the plain, unfiltered listing — a `search` query
    # is a one-off lookup, not something worth a shared cache entry for.
    if search is None:
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=3600"
    service = SchoolService(db)
    schools = await service.list_public(offset=offset, limit=limit, search=search)
    return [SchoolPublicResponse.model_validate(s) for s in schools]


@router.get("/match", response_model=SchoolPublicResponse)
async def match_school_by_email(
    email: str = Query(..., min_length=3, max_length=255),
    db: AsyncSession = Depends(get_db),
) -> SchoolPublicResponse:
    """
    Resolves a registration email to its university by domain. Used by the
    register flow to validate the email and auto-select the school before
    the person ever reaches the password step, instead of only discovering
    a mismatch at final submission.
    """
    service = SchoolService(db)
    try:
        school = await service.match_by_email(email)
    except SchoolError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SchoolPublicResponse.model_validate(school)


@router.get("/{school_id}", response_model=SchoolPublicResponse)
async def get_school(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SchoolPublicResponse:
    service = SchoolService(db)
    try:
        school = await service.get_public(school_id)
    except SchoolError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SchoolPublicResponse.model_validate(school)


# --- Admin endpoints — require UserRole.ADMIN via router-level dependency ---


@admin_router.get("", response_model=list[SchoolAdminResponse])
async def admin_list_schools(
    status_filter: SchoolStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[SchoolAdminResponse]:
    service = SchoolService(db)
    schools = await service.list_for_admin(offset=offset, limit=limit, status=status_filter)
    return [SchoolAdminResponse.model_validate(s) for s in schools]


@admin_router.post("", response_model=SchoolAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_school(
    payload: SchoolCreateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SchoolAdminResponse:
    service = SchoolService(db)
    try:
        school = await service.create(
            admin=admin,
            name=payload.name,
            country=payload.country,
            city=payload.city,
            email_domain=payload.email_domain,
            logo_url=payload.logo_url,
        )
        await db.commit()
    except SchoolError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return SchoolAdminResponse.model_validate(school)


@admin_router.get("/{school_id}", response_model=SchoolAdminResponse)
async def admin_get_school(
    school_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SchoolAdminResponse:
    service = SchoolService(db)
    try:
        school = await service.get_for_admin(school_id)
    except SchoolError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SchoolAdminResponse.model_validate(school)


@admin_router.patch("/{school_id}", response_model=SchoolAdminResponse)
async def admin_update_school(
    school_id: uuid.UUID,
    payload: SchoolUpdateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SchoolAdminResponse:
    service = SchoolService(db)
    try:
        school = await service.update(
            admin=admin,
            school_id=school_id,
            name=payload.name,
            country=payload.country,
            city=payload.city,
            logo_url=payload.logo_url,
        )
        await db.commit()
    except SchoolError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SchoolAdminResponse.model_validate(school)


@admin_router.patch("/{school_id}/approve", response_model=SchoolAdminResponse)
async def admin_approve_school(
    school_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SchoolAdminResponse:
    service = SchoolService(db)
    try:
        school = await service.approve(admin=admin, school_id=school_id)
        await db.commit()
    except SchoolError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return SchoolAdminResponse.model_validate(school)


@admin_router.patch("/{school_id}/suspend", response_model=SchoolAdminResponse)
async def admin_suspend_school(
    school_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SchoolAdminResponse:
    service = SchoolService(db)
    try:
        school = await service.suspend(admin=admin, school_id=school_id)
        await db.commit()
    except SchoolError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return SchoolAdminResponse.model_validate(school)
