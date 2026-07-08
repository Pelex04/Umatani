"""Integration tests for the reviews module."""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User, UserRole, UserStatus
from app.modules.businesses.models import Business, BusinessStatus
from app.modules.categories.models import Category
from app.modules.schools.models import School

pytestmark = pytest.mark.asyncio
VALID_PASSWORD = "ValidPass123"


async def _make_approved_business(
    db_session: AsyncSession,
    owner: User,
    school: School,
    category: Category,
    name: str = "Test Biz",
) -> Business:
    from app.modules.categories.schemas import slugify
    biz = Business(
        id=uuid.uuid4(), owner_id=owner.id, school_id=school.id,
        category_id=category.id, name=name,
        slug=slugify(name), description="A test business with enough description",
        status=BusinessStatus.APPROVED,
    )
    db_session.add(biz)
    await db_session.flush()
    await db_session.commit()
    return biz


async def _make_reviewer(
    db_session: AsyncSession, school: School, email: str
) -> tuple["User", str]:
    from app.core.security import create_access_token, hash_password
    reviewer = User(
        id=uuid.uuid4(), email=email,
        hashed_password=hash_password(VALID_PASSWORD),
        full_name="Reviewer",
        role=UserRole.BUSINESS_OWNER, status=UserStatus.VERIFIED,
        school_id=school.id,
    )
    db_session.add(reviewer)
    await db_session.flush()
    await db_session.commit()
    token = create_access_token(str(reviewer.id), reviewer.role)
    return reviewer, token


class TestReviewCreation:
    async def test_authenticated_user_can_review_approved_business(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, verified_owner_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category)
        reviewer, token = await _make_reviewer(db_session, approved_school, "rev1@mubas.ac.mw")

        resp = await app_client.post(
            "/api/v1/reviews",
            json={
                "business_id": str(biz.id),
                "rating": 5,
                "comment": "Excellent graphic design work, very professional!",
                "service_received": "Logo Design",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["rating"] == 5
        assert body["reply"] is None

    async def test_unauthenticated_user_cannot_review(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category, verified_owner: User,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category)
        resp = await app_client.post(
            "/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 4,
                  "comment": "Good work done here really great"},
        )
        assert resp.status_code == 401

    async def test_owner_cannot_review_own_business(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, verified_owner_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category)
        resp = await app_client.post(
            "/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 5,
                  "comment": "My own business is absolutely amazing!"},
            headers=verified_owner_headers,
        )
        assert resp.status_code == 400
        assert "own business" in resp.json()["detail"]

    async def test_duplicate_review_rejected(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category, verified_owner: User,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category)
        reviewer, token = await _make_reviewer(db_session, approved_school, "rev2@mubas.ac.mw")

        payload = {"business_id": str(biz.id), "rating": 4,
                   "comment": "Really great work done here well"}
        await app_client.post("/api/v1/reviews", json=payload,
                              headers={"Authorization": f"Bearer {token}"})
        resp = await app_client.post("/api/v1/reviews", json=payload,
                                     headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400
        assert "already reviewed" in resp.json()["detail"]

    async def test_rating_updates_business_average(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category, verified_owner: User,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category, name="Rating Test Biz")
        r1, t1 = await _make_reviewer(db_session, approved_school, "rev3@mubas.ac.mw")
        r2, t2 = await _make_reviewer(db_session, approved_school, "rev4@mubas.ac.mw")

        await app_client.post("/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 4, "comment": "Good work very well done"},
            headers={"Authorization": f"Bearer {t1}"})
        await app_client.post("/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 2, "comment": "Not great at all really"},
            headers={"Authorization": f"Bearer {t2}"})

        biz_resp = await app_client.get(f"/api/v1/businesses/{biz.id}")
        body = biz_resp.json()
        assert body["review_count"] == 2
        assert body["average_rating"] == 3.0


class TestReviewReply:
    async def test_owner_can_reply_to_review(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, verified_owner_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category, name="Reply Test Biz")
        reviewer, token = await _make_reviewer(db_session, approved_school, "rev5@mubas.ac.mw")

        review_resp = await app_client.post(
            "/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 3,
                  "comment": "Decent work but could be better quality"},
            headers={"Authorization": f"Bearer {token}"},
        )
        review_id = review_resp.json()["id"]

        reply_resp = await app_client.post(
            f"/api/v1/reviews/{review_id}/reply",
            json={"content": "Thank you for your feedback, we will improve!"},
            headers=verified_owner_headers,
        )
        assert reply_resp.status_code == 200
        assert reply_resp.json()["reply"]["content"] == "Thank you for your feedback, we will improve!"

    async def test_double_reply_rejected(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, verified_owner_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category, name="Double Reply Biz")
        reviewer, token = await _make_reviewer(db_session, approved_school, "rev6@mubas.ac.mw")
        review_resp = await app_client.post(
            "/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 3,
                  "comment": "Decent service but room for improvement"},
            headers={"Authorization": f"Bearer {token}"},
        )
        review_id = review_resp.json()["id"]
        await app_client.post(f"/api/v1/reviews/{review_id}/reply",
                              json={"content": "Thanks for the feedback!"},
                              headers=verified_owner_headers)
        resp = await app_client.post(f"/api/v1/reviews/{review_id}/reply",
                                     json={"content": "Another reply attempt"},
                                     headers=verified_owner_headers)
        assert resp.status_code == 400


class TestReviewModeration:
    async def test_admin_can_flag_review(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, admin_auth_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category, name="Flag Test Biz")
        reviewer, token = await _make_reviewer(db_session, approved_school, "rev7@mubas.ac.mw")
        review_resp = await app_client.post(
            "/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 1,
                  "comment": "Spam review with fake information here"},
            headers={"Authorization": f"Bearer {token}"},
        )
        review_id = review_resp.json()["id"]

        flag_resp = await app_client.patch(
            f"/api/v1/admin/reviews/{review_id}/flag", headers=admin_auth_headers
        )
        assert flag_resp.status_code == 200
        assert flag_resp.json()["is_flagged"] is True

        # Flagged review must not appear in public listing
        list_resp = await app_client.get(f"/api/v1/reviews?business_id={biz.id}")
        ids = [r["id"] for r in list_resp.json()["items"]]
        assert review_id not in ids

    async def test_flagging_updates_business_rating(
        self, app_client: AsyncClient, db_session: AsyncSession,
        approved_school: School, active_category: Category,
        verified_owner: User, admin_auth_headers: dict,
    ) -> None:
        biz = await _make_approved_business(db_session, verified_owner, approved_school, active_category, name="Rating Flag Biz")
        r1, t1 = await _make_reviewer(db_session, approved_school, "rev8@mubas.ac.mw")
        r2, t2 = await _make_reviewer(db_session, approved_school, "rev9@mubas.ac.mw")

        await app_client.post("/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 5,
                  "comment": "Perfect work done very well indeed"},
            headers={"Authorization": f"Bearer {t1}"})
        bad = await app_client.post("/api/v1/reviews",
            json={"business_id": str(biz.id), "rating": 1,
                  "comment": "Fake spam review should be removed"},
            headers={"Authorization": f"Bearer {t2}"})
        review_id = bad.json()["id"]

        await app_client.patch(f"/api/v1/admin/reviews/{review_id}/flag",
                               headers=admin_auth_headers)

        biz_resp = await app_client.get(f"/api/v1/businesses/{biz.id}")
        assert biz_resp.json()["review_count"] == 1
        assert biz_resp.json()["average_rating"] == 5.0
