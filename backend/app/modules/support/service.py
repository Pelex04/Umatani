import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.support.models import Report, ReportStatus, ReportType, SupportTicket, TicketStatus
from app.shared.audit_service import record_audit_event


class SupportError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_report(
        self, *, reporter_id: uuid.UUID | None, report_type: ReportType,
        target_id: str, reason: str, details: str | None,
    ) -> Report:
        report = Report(
            report_type=report_type, target_id=target_id,
            reporter_id=reporter_id, reason=reason, details=details,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def create_ticket(
        self, *, user: User, ticket_type, subject: str, description: str,
    ) -> SupportTicket:
        ticket = SupportTicket(
            ticket_type=ticket_type, submitter_id=user.id,
            subject=subject, description=description,
        )
        self.db.add(ticket)
        await self.db.flush()
        return ticket

    async def get_own_tickets(self, user: User) -> list[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket)
            .where(SupportTicket.submitter_id == user.id)
            .order_by(SupportTicket.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_reports(
        self, *, status: ReportStatus | None = None, offset: int = 0, limit: int = 50
    ) -> list[Report]:
        stmt = select(Report)
        if status:
            stmt = stmt.where(Report.status == status)
        stmt = stmt.order_by(Report.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_tickets(
        self, *, status: TicketStatus | None = None, offset: int = 0, limit: int = 50
    ) -> list[SupportTicket]:
        stmt = select(SupportTicket)
        if status:
            stmt = stmt.where(SupportTicket.status == status)
        stmt = stmt.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def resolve_report(
        self, *, admin: User, report_id: uuid.UUID,
        status: ReportStatus, admin_note: str | None,
    ) -> Report:
        report = await self.db.get(Report, report_id)
        if report is None:
            raise SupportError("Report not found")
        report.status = status
        report.admin_note = admin_note
        if status != ReportStatus.OPEN:
            report.resolved_at = datetime.now(UTC)
        await self.db.flush()
        await record_audit_event(
            self.db, action=f"report.{status.value}", resource_type="report",
            resource_id=str(report_id), actor_id=admin.id, actor_role=admin.role,
        )
        return report

    async def respond_ticket(
        self, *, admin: User, ticket_id: uuid.UUID,
        status: TicketStatus, admin_response: str | None,
    ) -> SupportTicket:
        ticket = await self.db.get(SupportTicket, ticket_id)
        if ticket is None:
            raise SupportError("Ticket not found")
        ticket.status = status
        ticket.admin_response = admin_response
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket
