"""Integration tests for support module and admin dashboard."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


class TestReports:
    async def test_anyone_can_submit_report(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/support/reports",
            json={"report_type": "business", "target_id": "some-biz-id",
                  "reason": "This business is fraudulent and fake"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "open"

    async def test_admin_can_resolve_report(
        self, app_client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        report_resp = await app_client.post(
            "/api/v1/support/reports",
            json={"report_type": "scam", "target_id": "some-id",
                  "reason": "Confirmed scam activity on the platform"},
        )
        report_id = report_resp.json()["id"]

        resolve_resp = await app_client.patch(
            f"/api/v1/admin/support/reports/{report_id}",
            json={"status": "resolved", "admin_note": "Confirmed and business suspended"},
            headers=admin_auth_headers,
        )
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resolved"

    async def test_admin_can_list_open_reports(
        self, app_client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        await app_client.post(
            "/api/v1/support/reports",
            json={"report_type": "review", "target_id": "review-id",
                  "reason": "This review contains false information"},
        )
        resp = await app_client.get(
            "/api/v1/admin/support/reports?status=open", headers=admin_auth_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestSupportTickets:
    async def test_authenticated_user_can_submit_ticket(
        self, app_client: AsyncClient, verified_owner_headers: dict
    ) -> None:
        resp = await app_client.post(
            "/api/v1/support/tickets",
            json={
                "ticket_type": "support",
                "subject": "Cannot upload my student ID",
                "description": "I have been trying to upload my student ID but the upload keeps failing with an error message about file size even though the file is small.",
            },
            headers=verified_owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "open"

    async def test_user_can_view_own_tickets(
        self, app_client: AsyncClient, verified_owner_headers: dict
    ) -> None:
        await app_client.post(
            "/api/v1/support/tickets",
            json={
                "ticket_type": "feature_request",
                "subject": "Add video portfolio support",
                "description": "It would be great to embed YouTube videos directly in the portfolio section for music and performance artists.",
            },
            headers=verified_owner_headers,
        )
        resp = await app_client.get("/api/v1/support/tickets/mine", headers=verified_owner_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_admin_can_respond_to_ticket(
        self, app_client: AsyncClient,
        verified_owner_headers: dict, admin_auth_headers: dict
    ) -> None:
        ticket_resp = await app_client.post(
            "/api/v1/support/tickets",
            json={
                "ticket_type": "support",
                "subject": "How do I add portfolio items?",
                "description": "I cannot figure out how to add images to my portfolio. The button does not seem to be working on my phone browser.",
            },
            headers=verified_owner_headers,
        )
        ticket_id = ticket_resp.json()["id"]

        resp = await app_client.patch(
            f"/api/v1/admin/support/tickets/{ticket_id}",
            json={"status": "resolved",
                  "admin_response": "Upload images via the media section first, then add them to your portfolio from the business dashboard."},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"
        assert resp.json()["admin_response"] is not None


class TestAdminDashboard:
    async def test_platform_stats_returns_counts(
        self, app_client: AsyncClient, admin_auth_headers: dict,
        verified_owner: "User",
    ) -> None:
        resp = await app_client.get("/api/v1/admin/stats", headers=admin_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "total_users" in body
        assert "total_businesses" in body
        assert "open_reports" in body
        assert body["total_users"] >= 1

    async def test_non_admin_cannot_access_stats(
        self, app_client: AsyncClient, verified_owner_headers: dict
    ) -> None:
        resp = await app_client.get("/api/v1/admin/stats", headers=verified_owner_headers)
        assert resp.status_code == 403

    async def test_admin_can_list_users(
        self, app_client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        resp = await app_client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_admin_can_verify_user(
        self, app_client: AsyncClient, db_session: AsyncSession,
        admin_auth_headers: dict, approved_school: "School",
    ) -> None:
        from app.core.security import hash_password
        from app.modules.auth.models import User, UserRole, UserStatus
        import uuid

        pending = User(
            id=uuid.uuid4(), email="pending@mubas.ac.mw",
            hashed_password=hash_password("Pass123word"),
            full_name="Pending Student", role=UserRole.BUSINESS_OWNER,
            status=UserStatus.PENDING_ID_REVIEW, school_id=approved_school.id,
        )
        db_session.add(pending)
        await db_session.commit()

        resp = await app_client.patch(
            f"/api/v1/admin/users/{pending.id}/verify", headers=admin_auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"

    async def test_admin_can_view_audit_logs(
        self, app_client: AsyncClient, admin_auth_headers: dict,
        approved_school: "School",
    ) -> None:
        # Trigger an auditable action first
        await app_client.patch(
            f"/api/v1/admin/schools/{approved_school.id}/approve",
            headers=admin_auth_headers,
        )  # will fail (already approved) but that's fine

        resp = await app_client.get("/api/v1/admin/audit-logs", headers=admin_auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
