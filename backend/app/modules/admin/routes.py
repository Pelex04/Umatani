"""
Admin dashboard routes.

Provides aggregated analytics and cross-module management views.
All routes require UserRole.ADMIN.
"""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.auth.models import User, UserRole, UserStatus
from app.modules.businesses.models import Business, BusinessStatus
from app.modules.categories.models import Category
from app.modules.reviews.models import Review
from app.modules.schools.models import School, SchoolStatus
from app.modules.support.models import Report, ReportStatus, SupportTicket, TicketStatus
from app.shared.audit import AuditLog

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


class PlatformStats(BaseModel):
    total_users: int
    verified_users: int
    pending_id_review: int
    total_businesses: int
    pending_businesses: int
    approved_businesses: int
    total_schools: int
    approved_schools: int
    total_reviews: int
    flagged_reviews: int
    open_reports: int
    open_tickets: int


class UserAdminResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    status: str
    school_id: str | None
    student_id_submitted: bool
    created_at: datetime


@router.get("/stats", response_model=PlatformStats)
async def platform_stats(db: AsyncSession = Depends(get_db)) -> PlatformStats:
    async def count(model, *filters):
        result = await db.execute(select(func.count()).select_from(
            select(model).where(*filters).subquery()
        ))
        return result.scalar_one()

    return PlatformStats(
        total_users=await count(User, User.role == UserRole.BUSINESS_OWNER),
        verified_users=await count(User, User.status == UserStatus.VERIFIED),
        pending_id_review=await count(User, User.status == UserStatus.PENDING_ID_REVIEW),
        total_businesses=await count(Business),
        pending_businesses=await count(Business, Business.status == BusinessStatus.PENDING),
        approved_businesses=await count(Business, Business.status == BusinessStatus.APPROVED),
        total_schools=await count(School),
        approved_schools=await count(School, School.status == SchoolStatus.APPROVED),
        total_reviews=await count(Review),
        flagged_reviews=await count(Review, Review.is_flagged.is_(True)),
        open_reports=await count(Report, Report.status == ReportStatus.OPEN),
        open_tickets=await count(SupportTicket, SupportTicket.status == TicketStatus.OPEN),
    )


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    role: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[UserAdminResponse]:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [
        UserAdminResponse(
            id=str(u.id), email=u.email, full_name=u.full_name,
            role=u.role, status=u.status,
            school_id=str(u.school_id) if u.school_id else None,
            student_id_submitted=u.student_id_storage_key is not None,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/users/{user_id}/suspend", response_model=UserAdminResponse)
async def suspend_user(
    user_id: str,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserAdminResponse:
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID") from exc

    user = await db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend yourself")

    user.status = UserStatus.SUSPENDED
    await db.commit()
    return UserAdminResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        role=user.role, status=user.status,
        school_id=str(user.school_id) if user.school_id else None,
        student_id_submitted=user.student_id_storage_key is not None,
        created_at=user.created_at,
    )


@router.patch("/users/{user_id}/verify", response_model=UserAdminResponse)
async def verify_user(
    user_id: str,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserAdminResponse:
    """Admin approves a student ID submission, promoting the user to VERIFIED."""
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID") from exc

    user = await db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.status != UserStatus.PENDING_ID_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User status is '{user.status}', expected 'pending_id_review'",
        )
    if user.student_id_storage_key is None:
        # pending_id_review covers both "needs to submit an ID" and
        # "submitted, awaiting review" — without this check an admin could
        # approve someone who has no ID on file at all, defeating the
        # purpose of ID verification entirely.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has not submitted a student ID yet",
        )
    user.status = UserStatus.VERIFIED
    user.id_verified_at = datetime.now(UTC)
    await db.commit()

    from app.core.email import send_approval_email
    await send_approval_email(to=user.email, full_name=user.full_name)

    return UserAdminResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        role=user.role, status=user.status,
        school_id=str(user.school_id) if user.school_id else None,
        student_id_submitted=user.student_id_storage_key is not None,
        created_at=user.created_at,
    )


@router.get("/audit-logs")
async def list_audit_logs(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "actor_id": str(log.actor_id) if log.actor_id else None,
            "actor_role": log.actor_role,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "metadata": log.metadata_,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
