"""
Schools service layer.

Security/business rules enforced here:
- email_domain must be globally unique — two schools sharing a domain
  would let a business owner register under the wrong school's identity.
- Newly created schools start PENDING and are not visible to visitors
  or selectable at registration until explicitly approved by an admin —
  this exists so a malicious actor can't self-create a fake "school"
  with a domain they control and use it to bypass verification.
- Suspending a school does not retroactively unverify existing business
  owners; it only blocks new registrations (handled by AuthService,
  which checks status == APPROVED and is_active == True at registration
  time).
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.schools.models import School, SchoolStatus
from app.modules.schools.repository import SchoolRepository
from app.shared.audit_service import record_audit_event


class SchoolError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SchoolService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.schools = SchoolRepository(db)

    async def list_public(
        self, *, offset: int = 0, limit: int = 50, search: str | None = None
    ) -> list[School]:
        return await self.schools.list_public(offset=offset, limit=limit, search=search)

    async def get_public(self, school_id: uuid.UUID) -> School:
        school = await self.schools.get_by_id(school_id)
        if (
            school is None
            or school.status != SchoolStatus.APPROVED
            or not school.is_active
        ):
            raise SchoolError("School not found")
        return school

    async def get_for_admin(self, school_id: uuid.UUID) -> School:
        school = await self.schools.get_by_id(school_id)
        if school is None:
            raise SchoolError("School not found")
        return school

    async def list_for_admin(
        self, *, offset: int = 0, limit: int = 50, status: SchoolStatus | None = None
    ) -> list[School]:
        filters = {"status": status} if status is not None else {}
        return await self.schools.list(offset=offset, limit=limit, **filters)

    async def create(
        self,
        *,
        admin: User,
        name: str,
        country: str,
        city: str,
        email_domain: str,
        logo_url: str | None,
    ) -> School:
        existing = await self.schools.get_by_domain(email_domain)
        if existing is not None:
            raise SchoolError(f"A school with domain '{email_domain}' already exists")

        school = await self.schools.create(
            name=name,
            country=country,
            city=city,
            email_domain=email_domain,
            logo_url=logo_url,
            status=SchoolStatus.PENDING,
            is_active=True,
        )

        await record_audit_event(
            self.db,
            action="school.created",
            resource_type="school",
            resource_id=str(school.id),
            actor_id=admin.id,
            actor_role=admin.role,
            metadata={"name": name, "email_domain": email_domain},
        )
        return school

    async def update(
        self,
        *,
        admin: User,
        school_id: uuid.UUID,
        name: str | None = None,
        country: str | None = None,
        city: str | None = None,
        logo_url: str | None = None,
    ) -> School:
        school = await self.get_for_admin(school_id)
        updates = {
            k: v
            for k, v in {
                "name": name,
                "country": country,
                "city": city,
                "logo_url": logo_url,
            }.items()
            if v is not None
        }
        if updates:
            school = await self.schools.update(school, **updates)
            await record_audit_event(
                self.db,
                action="school.updated",
                resource_type="school",
                resource_id=str(school.id),
                actor_id=admin.id,
                actor_role=admin.role,
                metadata=updates,
            )
        return school

    async def approve(self, *, admin: User, school_id: uuid.UUID) -> School:
        school = await self.get_for_admin(school_id)
        if school.status == SchoolStatus.APPROVED:
            raise SchoolError("School is already approved")

        school = await self.schools.update(school, status=SchoolStatus.APPROVED)
        await record_audit_event(
            self.db,
            action="school.approved",
            resource_type="school",
            resource_id=str(school.id),
            actor_id=admin.id,
            actor_role=admin.role,
        )
        return school

    async def suspend(self, *, admin: User, school_id: uuid.UUID) -> School:
        school = await self.get_for_admin(school_id)
        school = await self.schools.update(school, status=SchoolStatus.SUSPENDED)
        await record_audit_event(
            self.db,
            action="school.suspended",
            resource_type="school",
            resource_id=str(school.id),
            actor_id=admin.id,
            actor_role=admin.role,
        )
        return school
