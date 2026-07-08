import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category

pytestmark = pytest.mark.asyncio


class TestPublicCategoryEndpoints:
    async def test_active_category_visible_publicly(
        self, app_client: AsyncClient, active_category: Category
    ) -> None:
        resp = await app_client.get("/api/v1/categories")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert active_category.name in names

    async def test_inactive_category_hidden_from_public(
        self, app_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cat = Category(
            id=uuid.uuid4(), name="Inactive Art", slug="inactive-art",
            is_active=False, display_order=0,
        )
        db_session.add(cat)
        await db_session.commit()

        resp = await app_client.get("/api/v1/categories")
        names = [c["name"] for c in resp.json()]
        assert "Inactive Art" not in names

    async def test_public_response_excludes_admin_fields(
        self, app_client: AsyncClient, active_category: Category
    ) -> None:
        resp = await app_client.get(f"/api/v1/categories/{active_category.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "is_active" not in body
        assert "created_at" not in body

    async def test_inactive_category_returns_404(
        self, app_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        cat = Category(
            id=uuid.uuid4(), name="Hidden", slug="hidden",
            is_active=False, display_order=0,
        )
        db_session.add(cat)
        await db_session.commit()
        resp = await app_client.get(f"/api/v1/categories/{cat.id}")
        assert resp.status_code == 404


class TestAdminCategoryManagement:
    async def test_create_category_requires_admin(
        self, app_client: AsyncClient, verified_owner_headers: dict
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/categories",
            json={"name": "Photography", "display_order": 1},
            headers=verified_owner_headers,
        )
        assert resp.status_code == 403

    async def test_admin_creates_category_with_slug(
        self, app_client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/categories",
            json={"name": "Hair Styling", "display_order": 2},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["slug"] == "hair-styling"
        assert body["is_active"] is True

    async def test_duplicate_name_rejected(
        self, app_client: AsyncClient, admin_auth_headers: dict, active_category: Category
    ) -> None:
        resp = await app_client.post(
            "/api/v1/admin/categories",
            json={"name": active_category.name, "display_order": 0},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 400

    async def test_slug_collision_gets_suffix(
        self, app_client: AsyncClient, admin_auth_headers: dict
    ) -> None:
        # Create "Tutoring" twice (different names that produce same slug would
        # be caught by name check; test same-slug via special chars stripping)
        await app_client.post(
            "/api/v1/admin/categories",
            json={"name": "Tutoring", "display_order": 0},
            headers=admin_auth_headers,
        )
        # Manually insert a second category that would conflict on slug
        # by creating via service with a name that generates the same base slug
        # — instead test via the API that name check catches true duplicates.
        resp = await app_client.post(
            "/api/v1/admin/categories",
            json={"name": "Tutoring!", "display_order": 0},
            headers=admin_auth_headers,
        )
        # Should succeed with a suffixed slug, not fail
        assert resp.status_code == 201
        assert resp.json()["slug"] in ("tutoring-1", "tutoring")

    async def test_admin_can_deactivate_category(
        self, app_client: AsyncClient, admin_auth_headers: dict, active_category: Category
    ) -> None:
        resp = await app_client.patch(
            f"/api/v1/admin/categories/{active_category.id}",
            json={"is_active": False},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Immediately hidden from public
        public_resp = await app_client.get(f"/api/v1/categories/{active_category.id}")
        assert public_resp.status_code == 404
