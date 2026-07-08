import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schools.models import School
from tests.conftest import SAMPLE_PNG_BYTES

pytestmark = pytest.mark.asyncio

VALID_PASSWORD = "ValidPass123"


async def _register_and_get_access_token(
    app_client: AsyncClient, school: School, email: str = "rasta@mubas.ac.mw"
) -> str:
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "full_name": "Rasta Kadema",
            "school_id": str(school.id),
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD}
    )
    return login_resp.json()["access_token"]


class TestMediaUpload:
    async def test_upload_requires_authentication(self, app_client: AsyncClient) -> None:
        resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "business_logo"},
            files={"file": ("logo.png", SAMPLE_PNG_BYTES, "image/png")},
        )
        assert resp.status_code == 401

    async def test_authenticated_upload_succeeds(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)

        resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "business_logo"},
            files={"file": ("logo.png", SAMPLE_PNG_BYTES, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["purpose"] == "business_logo"
        assert body["storage_key"].startswith("business_logo/")

    async def test_upload_rejects_content_mismatched_with_claimed_type(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)

        malicious = b"<html><script>alert(document.cookie)</script></html>"
        resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "business_logo"},
            # Client claims this is a PNG via Content-Type and filename —
            # server must catch the mismatch via content sniffing.
            files={"file": ("totally_a_logo.png", malicious, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    async def test_upload_rejects_pdf_for_logo_purpose(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)
        pdf_bytes = b"%PDF-1.4\n" + b"\x00" * 50

        resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "business_logo"},
            files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    async def test_storage_key_is_namespaced_by_uploading_user(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)

        resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "student_id"},
            files={"file": ("id.png", SAMPLE_PNG_BYTES, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        storage_key = resp.json()["storage_key"]

        me_resp = await app_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        user_id = me_resp.json()["id"]
        assert storage_key.startswith(f"student_id/{user_id}/")


class TestAdminSignedUrl:
    async def test_signed_url_requires_admin(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)
        resp = await app_client.get(
            "/api/v1/admin/media/signed-url",
            params={"storage_key": "student_id/abc/fake.jpg"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_get_signed_url_for_existing_object(
        self,
        app_client: AsyncClient,
        approved_school: School,
        admin_auth_headers: dict[str, str],
    ) -> None:
        token = await _register_and_get_access_token(app_client, approved_school)
        upload_resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "student_id"},
            files={"file": ("id.png", SAMPLE_PNG_BYTES, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        storage_key = upload_resp.json()["storage_key"]

        signed_resp = await app_client.get(
            "/api/v1/admin/media/signed-url",
            params={"storage_key": storage_key},
            headers=admin_auth_headers,
        )
        assert signed_resp.status_code == 200
        assert "url" in signed_resp.json()


class TestStudentIdSubmissionEndToEnd:
    async def test_full_flow_upload_then_submit(
        self, app_client: AsyncClient, db_session: AsyncSession, approved_school: School
    ) -> None:
        from app.modules.auth.service import AuthService

        service = AuthService(db_session)
        user, raw_token = await service.register(
            email="rasta3@mubas.ac.mw",
            password=VALID_PASSWORD,
            full_name="Rasta Kadema",
            school_id=approved_school.id,
        )
        await db_session.commit()
        await service.verify_email(raw_token)
        await db_session.commit()

        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta3@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        access_token = login_resp.json()["access_token"]

        upload_resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "student_id"},
            files={"file": ("id.png", SAMPLE_PNG_BYTES, "image/png")},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        storage_key = upload_resp.json()["storage_key"]

        submit_resp = await app_client.post(
            "/api/v1/auth/student-id",
            params={"storage_key": storage_key},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "pending_id_review"

    async def test_fabricated_storage_key_rejected(
        self, app_client: AsyncClient, db_session: AsyncSession, approved_school: School
    ) -> None:
        """A user cannot claim someone else's key as their own student ID."""
        from app.modules.auth.service import AuthService

        service = AuthService(db_session)
        user, raw_token = await service.register(
            email="rasta4@mubas.ac.mw",
            password=VALID_PASSWORD,
            full_name="Rasta Kadema",
            school_id=approved_school.id,
        )
        await db_session.commit()
        await service.verify_email(raw_token)
        await db_session.commit()

        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta4@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        access_token = login_resp.json()["access_token"]

        fabricated_key = f"student_id/{uuid.uuid4()}/someone_elses_id.jpg"
        resp = await app_client.post(
            "/api/v1/auth/student-id",
            params={"storage_key": fabricated_key},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 400

    async def test_submit_rejected_before_email_verification(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        token = await _register_and_get_access_token(
            app_client, approved_school, email="rasta5@mubas.ac.mw"
        )

        upload_resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "student_id"},
            files={"file": ("id.png", SAMPLE_PNG_BYTES, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )
        storage_key = upload_resp.json()["storage_key"]

        resp = await app_client.post(
            "/api/v1/auth/student-id",
            params={"storage_key": storage_key},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Status is still PENDING_EMAIL_VERIFICATION, not PENDING_ID_REVIEW.
        assert resp.status_code == 400
