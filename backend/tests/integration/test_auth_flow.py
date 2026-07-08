import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User, UserStatus
from app.modules.schools.models import School

pytestmark = pytest.mark.asyncio


VALID_PASSWORD = "ValidPass123"


class TestRegistration:
    async def test_register_with_matching_school_domain_succeeds(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        resp = await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "rasta@mubas.ac.mw"
        assert body["status"] == "pending_email_verification"
        # Password hash must never appear anywhere in the response.
        assert "hashed_password" not in body
        assert "password" not in body
        assert "student_id_storage_key" not in body

    async def test_register_with_mismatched_domain_is_rejected(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        resp = await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@gmail.com",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        assert resp.status_code == 400
        assert "mubas.ac.mw" in resp.json()["detail"]

    async def test_register_with_weak_password_is_rejected(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        resp = await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": "alllowercase",  # no upper, no digit
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        assert resp.status_code == 422

    async def test_register_with_unknown_school_is_rejected(
        self, app_client: AsyncClient
    ) -> None:
        resp = await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 400

    async def test_duplicate_email_registration_is_rejected_generically(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        payload = {
            "email": "rasta@mubas.ac.mw",
            "password": VALID_PASSWORD,
            "full_name": "Rasta Kadema",
            "school_id": str(approved_school.id),
        }
        first = await app_client.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201

        second = await app_client.post("/api/v1/auth/register", json=payload)
        assert second.status_code == 400
        # Message must not confirm the account exists.
        assert "already" not in second.json()["detail"].lower()


class TestEmailVerificationAndLogin:
    async def test_login_blocked_until_email_verified_flow(
        self, app_client: AsyncClient, db_session: AsyncSession, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )

        # Login works even pre-verification per spec (verification gates
        # business actions like submitting a student ID, not login itself).
        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    async def test_login_with_wrong_password_fails(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": "WrongPassword1"},
        )
        assert resp.status_code == 401

    async def test_login_with_nonexistent_email_gives_generic_error(
        self, app_client: AsyncClient
    ) -> None:
        resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Incorrect email or password"

    async def test_account_locks_after_repeated_failed_logins(
        self, db_session: AsyncSession, approved_school: School
    ) -> None:
        """
        Exercises the account-lockout logic directly via the service layer.
        Lockout (5 failed attempts) and the HTTP-level rate limit on /login
        (5/minute) share the same threshold by design — defense in depth —
        which means an HTTP-level test would hit the rate limiter first
        rather than proving the lockout logic itself.
        """
        from app.modules.auth.service import AuthError, AuthService

        service = AuthService(db_session)
        await service.register(
            email="rasta@mubas.ac.mw",
            password=VALID_PASSWORD,
            full_name="Rasta Kadema",
            school_id=approved_school.id,
        )
        await db_session.commit()

        for _ in range(5):
            with pytest.raises(AuthError):
                await service.login(email="rasta@mubas.ac.mw", password="WrongPassword1")
            await db_session.commit()

        # 6th attempt, even with the CORRECT password, must be locked out.
        with pytest.raises(AuthError, match="locked"):
            await service.login(email="rasta@mubas.ac.mw", password=VALID_PASSWORD)

    async def test_full_email_verification_flow(
        self, app_client: AsyncClient, db_session: AsyncSession, approved_school: School
    ) -> None:
        from app.modules.auth.service import AuthService

        service = AuthService(db_session)
        user, raw_token = await service.register(
            email="rasta2@mubas.ac.mw",
            password=VALID_PASSWORD,
            full_name="Rasta Kadema",
            school_id=approved_school.id,
        )
        await db_session.commit()
        assert user.status == UserStatus.PENDING_EMAIL_VERIFICATION

        verified_user = await service.verify_email(raw_token)
        await db_session.commit()
        assert verified_user.status == UserStatus.PENDING_ID_REVIEW

        # Token is single-use — verifying again must fail.
        from app.modules.auth.service import AuthError

        with pytest.raises(AuthError):
            await service.verify_email(raw_token)


class TestRefreshTokenRotation:
    async def test_refresh_issues_new_tokens_and_revokes_old(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        old_refresh = login_resp.json()["refresh_token"]

        refresh_resp = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert new_tokens["refresh_token"] != old_refresh

        # Old refresh token must now be rejected (rotation/revocation).
        reuse_resp = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert reuse_resp.status_code == 401

    async def test_logout_revokes_refresh_token(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        refresh_token = login_resp.json()["refresh_token"]

        logout_resp = await app_client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )
        assert logout_resp.status_code == 204

        reuse_resp = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert reuse_resp.status_code == 401


class TestProtectedRoutes:
    async def test_me_requires_authentication(self, app_client: AsyncClient) -> None:
        resp = await app_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_returns_current_user_with_valid_token(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        access_token = login_resp.json()["access_token"]

        resp = await app_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "rasta@mubas.ac.mw"

    async def test_me_rejects_refresh_token_used_as_access_token(
        self, app_client: AsyncClient, approved_school: School
    ) -> None:
        await app_client.post(
            "/api/v1/auth/register",
            json={
                "email": "rasta@mubas.ac.mw",
                "password": VALID_PASSWORD,
                "full_name": "Rasta Kadema",
                "school_id": str(approved_school.id),
            },
        )
        login_resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": "rasta@mubas.ac.mw", "password": VALID_PASSWORD},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await app_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert resp.status_code == 401
