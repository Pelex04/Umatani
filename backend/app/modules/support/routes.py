import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.deps import get_current_user, require_role
from app.core.limiter import limiter

optional_bearer = HTTPBearer(auto_error=False)
from app.modules.auth.models import User, UserRole
from app.modules.support.models import ReportStatus, TicketStatus
from app.modules.support.schemas import (
    AdminReportUpdateRequest, AdminTicketUpdateRequest,
    ReportAdminResponse, ReportCreateRequest, ReportResponse,
    TicketCreateRequest, TicketResponse,
)
from app.modules.support.service import SupportError, SupportService

router = APIRouter(prefix="/support", tags=["support"])
admin_router = APIRouter(
    prefix="/admin/support", tags=["admin", "support"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().RATE_LIMIT_SUPPORT)
async def create_report(
    request: Request,
    payload: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> ReportResponse:
    # Resolve optional user without raising 401 if unauthenticated
    user: User | None = None
    if credentials is not None:
        try:
            from app.core.security import TokenType, decode_token
            payload_jwt = decode_token(credentials.credentials, TokenType.ACCESS)
            import uuid as _uuid
            from app.modules.auth.models import User as UserModel
            user_obj = await db.get(UserModel, _uuid.UUID(payload_jwt.sub))
            user = user_obj
        except Exception:
            pass
    service = SupportService(db)
    report = await service.create_report(
        reporter_id=user.id if user else None,
        report_type=payload.report_type,
        target_id=payload.target_id,
        reason=payload.reason,
        details=payload.details,
    )
    await db.commit()
    return ReportResponse.model_validate(report)


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().RATE_LIMIT_SUPPORT)
async def create_ticket(
    request: Request,
    payload: TicketCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    service = SupportService(db)
    ticket = await service.create_ticket(
        user=user,
        ticket_type=payload.ticket_type,
        subject=payload.subject,
        description=payload.description,
    )
    await db.commit()
    return TicketResponse.model_validate(ticket)


@router.get("/tickets/mine", response_model=list[TicketResponse])
async def my_tickets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TicketResponse]:
    service = SupportService(db)
    tickets = await service.get_own_tickets(user)
    return [TicketResponse.model_validate(t) for t in tickets]


@admin_router.get("/reports", response_model=list[ReportAdminResponse])
async def list_reports(
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ReportAdminResponse]:
    service = SupportService(db)
    reports = await service.list_reports(status=status_filter, offset=offset, limit=limit)
    return [ReportAdminResponse.model_validate(r) for r in reports]


@admin_router.patch("/reports/{report_id}", response_model=ReportAdminResponse)
async def resolve_report(
    report_id: uuid.UUID,
    payload: AdminReportUpdateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ReportAdminResponse:
    service = SupportService(db)
    try:
        report = await service.resolve_report(
            admin=admin, report_id=report_id,
            status=payload.status, admin_note=payload.admin_note,
        )
        await db.commit()
    except SupportError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ReportAdminResponse.model_validate(report)


@admin_router.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[TicketResponse]:
    service = SupportService(db)
    tickets = await service.list_tickets(status=status_filter, offset=offset, limit=limit)
    return [TicketResponse.model_validate(t) for t in tickets]


@admin_router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def respond_ticket(
    ticket_id: uuid.UUID,
    payload: AdminTicketUpdateRequest,
    admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    service = SupportService(db)
    try:
        ticket = await service.respond_ticket(
            admin=admin, ticket_id=ticket_id,
            status=payload.status, admin_response=payload.admin_response,
        )
        await db.commit()
    except SupportError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return TicketResponse.model_validate(ticket)
