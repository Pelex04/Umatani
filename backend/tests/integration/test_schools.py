import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schools.models import School, SchoolStatus

pytestmark = pytest.mark.asyncio


class TestPublicSchoolVisibility:
    async def test_approved_school_is_publicly_visible(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        resp = await app_client.get("/api/v1/schools")
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json()]
        assert approved_school.name in names

    async def test_pending_school_is_not_publicly_visible(
        self, app_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        pending = School(
            id=uuid.uuid4(),
            name="Unapproved University",
            country="Malawi",
            city="Zomba",
            email_domain="unapproved.ac.mw",
            status=SchoolStatus.PENDING,
            is_active=True,
        )
        db_session.add(pending)
        await db_session.commit()

        resp = await app_client.get("/api/v1/schools")
        names = [s["name"] for s in resp.json()]
        assert "Unapproved University" not in names

        detail_resp = await app_client.get(f"/api/v1/schools/{pending.id}")
        assert detail_resp.status_code == 404

    async def test_suspended_school_is_not_publicly_visible(
        self, app_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        suspended = School(
            id=uuid.uuid4(),
            name="Suspended College",
            country="Malawi",
            city="Mzuzu",
            email_domain="suspended.ac.mw",
            status=SchoolStatus.SUSPENDED,
            is_active=True,
        )
        db_session.add(suspended)
        await db_session.commit()

        resp = await app_client.get(f"/api/v1/schools/{suspended.id}")
        assert resp.status_code == 404

    async def test_public_school_response_excludes_admin_fields(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        resp = await app_client.get(f"/api/v1/schools/{approved_school.id}")
        body = resp.json()
        assert "status" not in body
        assert "is_active" not in body
        assert "email_domain" not in body

    async def test_search_filters_by_name(
        self, app_client: AsyncClient, approved_school: School, db_session: AsyncSession
    ) -> None:
        other = School(
            id=uuid.uuid4(),
            name="Chancellor College",
            country="Malawi",
            city="Zomba",
            email_domain="chanco.ac.mw",
            status=SchoolStatus.APPROVED,
            is_active=True,
        )
        db_session.add(other)
        await db_session.commit()

        resp = await app_client.get("/api/v1/schools", params={"search": "Chancellor"})
        names = [s["name"] for s in resp.json()]
        assert "Chancellor College" in names
        assert approved_school.name not in names


class TestAdminSchoolManagementRBAC:
    async def test_create_school_requires_authentication(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "newuni.ac.mw",
            },
        )
        assert resp.status_code == 401

    async def test_create_school_requires_admin_role(
        self, app_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        from app.core.security import create_access_token
        from app.modules.auth.models import User, UserRole, UserStatus

        non_admin = User(
            id=uuid.uuid4(),
            email="owner@mubas.ac.mw",
            hashed_password="irrelevant",
            full_name="Some Owner",
            role=UserRole.BUSINESS_OWNER,
            status=UserStatus.VERIFIED,
        )
        db_session.add(non_admin)
        await db_session.commit()
        token = create_access_token(str(non_admin.id), non_admin.role)

        resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "newuni.ac.mw",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_create_school(
        self, app_client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "newuni.ac.mw",
            },
            headers=admin_auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "pending"
        assert body["email_domain"] == "newuni.ac.mw"

    async def test_newly_created_school_not_publicly_visible_until_approved(
        self, app_client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        create_resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "newuni.ac.mw",
            },
            headers=admin_auth_headers,
        )
        school_id = create_resp.json()["id"]

        public_resp = await app_client.get(f"/api/v1/schools/{school_id}")
        assert public_resp.status_code == 404

    async def test_duplicate_email_domain_rejected(
        self, app_client: AsyncClient, admin_auth_headers: dict[str, str], approved_school: School
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "Duplicate Domain University",
                "country": "Malawi",
                "city": "Blantyre",
                "email_domain": approved_school.email_domain,
            },
            headers=admin_auth_headers,
        )
        assert resp.status_code == 400

    async def test_email_domain_normalized_with_at_prefix(
        self, app_client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "@newuni.ac.mw",
            },
            headers=admin_auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["email_domain"] == "newuni.ac.mw"


class TestApprovalWorkflow:
    async def test_approve_makes_school_publicly_visible(
        self, app_client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        create_resp = await app_client.post(
            "/api/v1/admin/schools",
            json={
                "name": "New University",
                "country": "Malawi",
                "city": "Lilongwe",
                "email_domain": "newuni.ac.mw",
            },
            headers=admin_auth_headers,
        )
        school_id = create_resp.json()["id"]

        approve_resp = await app_client.patch(
            f"/api/v1/admin/schools/{school_id}/approve", headers=admin_auth_headers
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        public_resp = await app_client.get(f"/api/v1/schools/{school_id}")
        assert public_resp.status_code == 200

    async def test_approving_already_approved_school_fails(
        self,
        app_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        approved_school: School,
    ) -> None:
        resp = await app_client.patch(
            f"/api/v1/admin/schools/{approved_school.id}/approve",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 400

    async def test_suspend_removes_public_visibility(
        self,
        app_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        approved_school: School,
    ) -> None:
        resp = await app_client.patch(
            f"/api/v1/admin/schools/{approved_school.id}/suspend",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"

        public_resp = await app_client.get(f"/api/v1/schools/{approved_school.id}")
        assert public_resp.status_code == 404

    async def test_registration_blocked_for_suspended_school(
        self,
        app_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        approved_school: School,
    ) -> None:
        await app_client.patch(
            f"/api/v1/admin/schools/{approved_school.id}/suspend",
            headers=admin_auth_headers,
        )

        resp = await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"student@{approved_school.email_domain}",
                "password": "ValidPass123",
                "full_name": "Some Student",
                "school_id": str(approved_school.id),
            },
        )
        assert resp.status_code == 400
