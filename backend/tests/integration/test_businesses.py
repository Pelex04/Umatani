"""
Integration tests for the Businesses module.

Covers: visibility rules, RBAC, ownership enforcement, the full
create→approve→visible flow, slug generation, the portfolio and services
sub-resources, and the storage-key ownership check on logo/cover/portfolio.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category
from app.modules.schools.models import School
from app.modules.auth.models import User
from tests.conftest import SAMPLE_PNG_BYTES

pytestmark = pytest.mark.asyncio

VALID_PASSWORD = "ValidPass123"
BASE_BUSINESS = {
    "name": "Rasta Designs",
    "description": "Professional graphic design for all your branding needs in Malawi",
    "services": [
        {"name": "Logo Design", "price_range": "MWK 5,000–15,000", "display_order": 0},
        {"name": "Poster Design", "price_range": "MWK 3,000–8,000", "display_order": 1},
    ],
}


async def _create_business(
    app_client: AsyncClient,
    owner_headers: dict,
    category: Category,
    **overrides,
) -> dict:
    payload = {**BASE_BUSINESS, "category_id": str(category.id), **overrides}
    resp = await app_client.post("/api/v1/businesses", json=payload, headers=owner_headers)
    return resp


class TestBusinessCreation:
    async def test_verified_owner_can_create_business(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        resp = await _create_business(app_client, verified_owner_headers, active_category)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Rasta Designs"
        assert body["status"] == "pending"
        assert body["slug"] == "rasta-designs"
        assert len(body["services"]) == 2

    async def test_unverified_owner_cannot_create_business(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
    ) -> None:
        from app.core.security import create_access_token
        from app.modules.auth.models import UserStatus

        unverified = User(
            id=uuid.uuid4(), email="new@mubas.ac.mw",
            hashed_password="x", full_name="New Student",
            role="business_owner", status=UserStatus.PENDING_ID_REVIEW,
            school_id=approved_school.id,
        )
        db_session.add(unverified)
        await db_session.commit()
        token = create_access_token(str(unverified.id), "business_owner")

        resp = await _create_business(
            app_client, {"Authorization": f"Bearer {token}"}, active_category
        )
        assert resp.status_code == 403  # get_verified_business_owner dep fires

    async def test_owner_cannot_create_second_business(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        resp = await _create_business(
            app_client, verified_owner_headers, active_category, name="Second Business"
        )
        assert resp.status_code == 400

    async def test_inactive_category_rejected(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        db_session: AsyncSession,
    ) -> None:
        inactive_cat = Category(
            id=uuid.uuid4(), name="Retired", slug="retired",
            is_active=False, display_order=0,
        )
        db_session.add(inactive_cat)
        await db_session.commit()

        resp = await _create_business(
            app_client, verified_owner_headers, inactive_cat
        )
        assert resp.status_code == 400

    async def test_description_too_short_rejected(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        resp = await _create_business(
            app_client, verified_owner_headers, active_category,
            description="Too short",
        )
        assert resp.status_code == 422


class TestBusinessVisibility:
    async def test_pending_business_not_visible_to_visitors(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        biz_id = create_resp.json()["id"]

        resp = await app_client.get(f"/api/v1/businesses/{biz_id}")
        assert resp.status_code == 404

    async def test_approved_business_visible_to_visitors(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        biz_id = create_resp.json()["id"]

        await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/approve",
            headers=admin_auth_headers,
        )

        resp = await app_client.get(f"/api/v1/businesses/{biz_id}")
        assert resp.status_code == 200
        body = resp.json()
        # Public response must not expose owner_id or status
        assert "owner_id" not in body
        assert "status" not in body

    async def test_approved_business_findable_by_slug(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        biz_id = create_resp.json()["id"]
        await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/approve", headers=admin_auth_headers
        )

        resp = await app_client.get("/api/v1/businesses/slug/rasta-designs")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Rasta Designs"

    async def test_suspended_business_not_visible_to_visitors(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        biz_id = create_resp.json()["id"]
        await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/approve", headers=admin_auth_headers
        )
        await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/suspend", headers=admin_auth_headers
        )

        resp = await app_client.get(f"/api/v1/businesses/{biz_id}")
        assert resp.status_code == 404

    async def test_search_returns_only_approved(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        resp = await app_client.get("/api/v1/businesses")
        assert resp.status_code == 200
        # No approved businesses yet — this pending one must not appear
        assert resp.json()["total"] == 0


class TestOwnerSelfService:
    async def test_owner_sees_own_pending_business(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        resp = await app_client.get("/api/v1/businesses/me", headers=verified_owner_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_owner_can_update_description(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        new_desc = "Updated description that is definitely longer than twenty characters"
        resp = await app_client.patch(
            "/api/v1/businesses/me",
            json={"description": new_desc},
            headers=verified_owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == new_desc

    async def test_owner_can_replace_services(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        resp = await app_client.patch(
            "/api/v1/businesses/me",
            json={"services": [{"name": "Branding Kit", "display_order": 0}]},
            headers=verified_owner_headers,
        )
        assert resp.status_code == 200
        services = resp.json()["services"]
        assert len(services) == 1
        assert services[0]["name"] == "Branding Kit"

    async def test_owner_cannot_update_another_owners_business(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        db_session: AsyncSession,
        approved_school: School,
    ) -> None:
        # Create business for the fixture owner
        await _create_business(app_client, verified_owner_headers, active_category)

        # Second owner tries to update via /me — they get their own 404
        from app.core.security import create_access_token
        from app.modules.auth.models import UserStatus

        other = User(
            id=uuid.uuid4(), email="other@mubas.ac.mw",
            hashed_password="x", full_name="Other Owner",
            role="business_owner", status=UserStatus.VERIFIED,
            school_id=approved_school.id,
        )
        db_session.add(other)
        await db_session.commit()
        other_token = create_access_token(str(other.id), "business_owner")

        resp = await app_client.patch(
            "/api/v1/businesses/me",
            json={"description": "Injected description that is long enough"},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        # /me scopes to their own business; other owner has no business yet → 404
        assert resp.status_code == 404


class TestLogoAndPortfolio:
    async def test_logo_with_valid_storage_key_succeeds(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        verified_owner: User,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)

        upload_resp = await app_client.post(
            "/api/v1/media/upload",
            data={"purpose": "business_logo"},
            files={"file": ("logo.png", SAMPLE_PNG_BYTES, "image/png")},
            headers=verified_owner_headers,
        )
        storage_key = upload_resp.json()["storage_key"]

        resp = await app_client.patch(
            f"/api/v1/businesses/me/logo?storage_key={storage_key}",
            headers=verified_owner_headers,
        )
        assert resp.status_code == 200
        # logo_storage_key is excluded from the response now (same private-
        # key-never-leaves-the-server pattern as student IDs); logo_url is
        # the computed field clients actually get, and should be populated
        # once a key has been set.
        assert resp.json()["logo_url"] is not None

    async def test_logo_with_fabricated_key_rejected(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)
        fake_key = f"business_logo/{uuid.uuid4()}/logo.png"
        resp = await app_client.patch(
            f"/api/v1/businesses/me/logo?storage_key={fake_key}",
            headers=verified_owner_headers,
        )
        assert resp.status_code == 400

    async def test_portfolio_item_added_and_removed(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)

        # External link doesn't need a storage key check
        add_resp = await app_client.post(
            "/api/v1/businesses/me/portfolio",
            json={
                "item_type": "external_link",
                "storage_key_or_url": "https://behance.net/rasta",
                "caption": "My Behance portfolio",
                "display_order": 0,
            },
            headers=verified_owner_headers,
        )
        assert add_resp.status_code == 201
        item_id = add_resp.json()["id"]

        delete_resp = await app_client.delete(
            f"/api/v1/businesses/me/portfolio/{item_id}",
            headers=verified_owner_headers,
        )
        assert delete_resp.status_code == 204


class TestAdminBusinessManagement:
    async def test_admin_can_list_pending_businesses(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        await _create_business(app_client, verified_owner_headers, active_category)

        resp = await app_client.get(
            "/api/v1/admin/businesses?status=pending", headers=admin_auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_approving_already_approved_fails(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        biz_id = create_resp.json()["id"]
        await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/approve", headers=admin_auth_headers
        )
        resp = await app_client.patch(
            f"/api/v1/admin/businesses/{biz_id}/approve", headers=admin_auth_headers
        )
        assert resp.status_code == 400

    async def test_search_filters_by_keyword(
        self,
        app_client: AsyncClient,
        verified_owner_headers: dict,
        active_category: Category,
        admin_auth_headers: dict,
    ) -> None:
        create_resp = await _create_business(
            app_client, verified_owner_headers, active_category
        )
        await app_client.patch(
            f"/api/v1/admin/businesses/{create_resp.json()['id']}/approve",
            headers=admin_auth_headers,
        )

        match = await app_client.get("/api/v1/businesses?keyword=Rasta")
        assert match.json()["total"] == 1

        no_match = await app_client.get("/api/v1/businesses?keyword=Plumbing")
        assert no_match.json()["total"] == 0
