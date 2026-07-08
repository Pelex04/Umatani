"""Helper for writing audit log entries from any module's service layer."""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.audit import AuditLog


async def record_audit_event(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    actor_id: uuid.UUID | None = None,
    actor_role: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Write an audit log entry. Does not commit — callers should already be
    inside a transaction managed by their own service/endpoint, so the
    audit entry commits atomically with the action it describes.
    """
    db.add(
        AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata,
            ip_address=ip_address,
        )
    )
    await db.flush()
