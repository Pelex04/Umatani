import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.support.models import ReportStatus, ReportType, TicketStatus, TicketType


class ReportCreateRequest(BaseModel):
    report_type: ReportType
    target_id: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=5, max_length=255)
    details: str | None = Field(default=None, max_length=2000)


class TicketCreateRequest(BaseModel):
    ticket_type: TicketType
    subject: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=20, max_length=5000)


class AdminReportUpdateRequest(BaseModel):
    status: ReportStatus
    admin_note: str | None = Field(default=None, max_length=2000)


class AdminTicketUpdateRequest(BaseModel):
    status: TicketStatus
    admin_response: str | None = Field(default=None, max_length=5000)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    report_type: ReportType
    target_id: str
    reason: str
    status: ReportStatus
    created_at: datetime


class ReportAdminResponse(ReportResponse):
    details: str | None
    reporter_id: uuid.UUID | None
    admin_note: str | None
    resolved_at: datetime | None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ticket_type: TicketType
    subject: str
    description: str
    status: TicketStatus
    admin_response: str | None
    created_at: datetime
    updated_at: datetime
