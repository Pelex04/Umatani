"""
Businesses service.

Key rules enforced here:

1. Only verified business owners may create a business. Status
   PENDING_EMAIL_VERIFICATION or PENDING_ID_REVIEW is not enough —
   an admin must have approved the student ID before a profile goes up.

2. One business per owner (V1). Attempting to create a second raises
   a descriptive error rather than silently overwriting.

3. Newly created businesses start PENDING and are invisible to visitors
   until an admin approves them, consistent with the spec's admin
   dashboard requirement for business management.

4. Owners may only edit their own business. The service layer enforces
   this so even if a route accidentally passed the wrong ID, the service
   would reject it.

5. Category must be active. A deactivated category means the admin
   no longer considers it valid — new profiles shouldn't be filed
   under it.

6. Slug is generated from business name and stays stable. If a name
   update would conflict it gets a numeric suffix, same as categories.

7. Portfolio items uploaded as IMAGE or DOCUMENT must have a storage key
   belonging to this owner and the correct purpose — key-ownership
   verification re-uses the same MediaService.verify_key_ownership check
   we built for student IDs.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User, UserStatus
from app.modules.businesses.models import (
    Business,
    BusinessStatus,
    PortfolioItem,
    PortfolioItemType,
)
from app.modules.businesses.repository import (
    BusinessRepository,
    PortfolioItemRepository,
    ServiceRepository,
)
from app.modules.categories.schemas import slugify as _slugify
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository
from app.modules.media.service import MediaService
from app.modules.media.validation import UploadPurpose
from app.shared.audit_service import record_audit_event


# re-export slugify for this module (businesses use the same logic)
def _slugify(name: str) -> str:
    from app.modules.categories.schemas import slugify
    return slugify(name)


class BusinessError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BusinessService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.businesses = BusinessRepository(db)
        self.services = ServiceRepository(db)
        self.portfolio = PortfolioItemRepository(db)
        self.categories = CategoryRepository(db)

    async def _unique_slug(self, base: str) -> str:
        candidate = base
        suffix = 1
        while True:
            existing = await self.businesses.get_by_slug(candidate)
            if existing is None:
                return candidate
            candidate = f"{base}-{suffix}"
            suffix += 1

    async def _assert_category_active(self, category_id: uuid.UUID) -> Category:
        cat = await self.categories.get_by_id(category_id)
        if cat is None or not cat.is_active:
            raise BusinessError("Selected category is not available")
        return cat

    # ------------------------------------------------------------------ #
    # Public (visitor) queries                                             #
    # ------------------------------------------------------------------ #

    async def search(
        self,
        *,
        keyword: str | None = None,
        category_id: uuid.UUID | None = None,
        school_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Business], int]:
        return await self.businesses.search(
            keyword=keyword,
            category_id=category_id,
            school_id=school_id,
            min_rating=min_rating,
            status=BusinessStatus.APPROVED,
            offset=offset,
            limit=limit,
        )

    async def get_public(self, business_id: uuid.UUID) -> Business:
        biz = await self.businesses.get_by_id_with_relations(business_id)
        if biz is None or biz.status != BusinessStatus.APPROVED:
            raise BusinessError("Business not found")
        return biz

    async def get_public_by_slug(self, slug: str) -> Business:
        biz = await self.businesses.get_by_slug(slug)
        if biz is None or biz.status != BusinessStatus.APPROVED:
            raise BusinessError("Business not found")
        return biz

    # ------------------------------------------------------------------ #
    # Owner actions                                                        #
    # ------------------------------------------------------------------ #

    async def create(
        self,
        *,
        owner: User,
        name: str,
        description: str,
        category_id: uuid.UUID,
        services_data: list[dict],
        **contact_fields,
    ) -> Business:
        if owner.status != UserStatus.VERIFIED:
            raise BusinessError(
                "Your account must be fully verified before creating a business profile"
            )

        existing = await self.businesses.get_by_owner(owner.id)
        if existing is not None:
            raise BusinessError("You already have a business profile")

        await self._assert_category_active(category_id)

        slug = await self._unique_slug(_slugify(name))

        biz = await self.businesses.create(
            owner_id=owner.id,
            school_id=owner.school_id,
            category_id=category_id,
            name=name,
            slug=slug,
            description=description,
            status=BusinessStatus.PENDING,
            **contact_fields,
        )

        if services_data:
            await self.services.replace_for_business(biz.id, services_data)

        await record_audit_event(
            self.db,
            action="business.created",
            resource_type="business",
            resource_id=str(biz.id),
            actor_id=owner.id,
            actor_role=owner.role,
            metadata={"name": name, "slug": slug},
        )
        # Reload with relations
        return await self.businesses.get_by_id_with_relations(biz.id)

    async def get_own(self, owner: User) -> Business:
        biz = await self.businesses.get_by_owner(owner.id)
        if biz is None:
            raise BusinessError("You do not have a business profile yet")
        return biz

    async def update(
        self,
        *,
        owner: User,
        updates: dict,
        services_data: list[dict] | None = None,
    ) -> Business:
        biz = await self.get_own(owner)

        if "category_id" in updates and updates["category_id"] is not None:
            await self._assert_category_active(updates["category_id"])

        if updates:
            biz = await self.businesses.update(biz, **updates)

        if services_data is not None:
            await self.services.replace_for_business(biz.id, services_data)

        await record_audit_event(
            self.db,
            action="business.updated",
            resource_type="business",
            resource_id=str(biz.id),
            actor_id=owner.id,
            actor_role=owner.role,
        )
        # After replacing services, explicitly refresh the business's
        # collections on the in-session object before returning, so
        # the response reflects the newly written rows.
        await self.db.refresh(biz, attribute_names=["services", "portfolio_items"])
        return biz

    async def update_logo(self, *, owner: User, storage_key: str) -> Business:
        biz = await self.get_own(owner)
        if not MediaService.verify_key_ownership(
            storage_key,
            expected_purpose=UploadPurpose.BUSINESS_LOGO,
            expected_owner_id=owner.id,
        ):
            raise BusinessError("Invalid storage key for business logo")
        biz = await self.businesses.update(biz, logo_storage_key=storage_key)
        return await self.businesses.get_by_id_with_relations(biz.id)

    async def update_cover(self, *, owner: User, storage_key: str) -> Business:
        biz = await self.get_own(owner)
        if not MediaService.verify_key_ownership(
            storage_key,
            expected_purpose=UploadPurpose.BUSINESS_COVER,
            expected_owner_id=owner.id,
        ):
            raise BusinessError("Invalid storage key for cover image")
        biz = await self.businesses.update(biz, cover_storage_key=storage_key)
        return await self.businesses.get_by_id_with_relations(biz.id)

    async def add_portfolio_item(
        self,
        *,
        owner: User,
        item_type: PortfolioItemType,
        storage_key_or_url: str,
        caption: str | None,
        display_order: int,
    ) -> PortfolioItem:
        biz = await self.get_own(owner)

        purpose_map = {
            PortfolioItemType.IMAGE: UploadPurpose.PORTFOLIO_IMAGE,
            PortfolioItemType.DOCUMENT: UploadPurpose.PORTFOLIO_DOCUMENT,
        }
        if item_type in purpose_map:
            if not MediaService.verify_key_ownership(
                storage_key_or_url,
                expected_purpose=purpose_map[item_type],
                expected_owner_id=owner.id,
            ):
                raise BusinessError("Invalid storage key for portfolio item")

        item = await self.portfolio.create(
            business_id=biz.id,
            item_type=item_type,
            storage_key_or_url=storage_key_or_url,
            caption=caption,
            display_order=display_order,
        )
        return item

    async def remove_portfolio_item(self, *, owner: User, item_id: uuid.UUID) -> None:
        biz = await self.get_own(owner)
        item = await self.portfolio.get_by_id(item_id)
        if item is None or item.business_id != biz.id:
            raise BusinessError("Portfolio item not found")
        await self.portfolio.delete(item)

    # ------------------------------------------------------------------ #
    # Admin actions                                                        #
    # ------------------------------------------------------------------ #

    async def admin_list(
        self,
        *,
        status: BusinessStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Business], int]:
        return await self.businesses.search(
            status=status or BusinessStatus.PENDING,
            offset=offset,
            limit=limit,
        )

    async def admin_get(self, business_id: uuid.UUID) -> Business:
        biz = await self.businesses.get_by_id_with_relations(business_id)
        if biz is None:
            raise BusinessError("Business not found")
        return biz

    async def approve(self, *, admin: User, business_id: uuid.UUID) -> Business:
        biz = await self.admin_get(business_id)
        if biz.status == BusinessStatus.APPROVED:
            raise BusinessError("Business is already approved")
        biz = await self.businesses.update(biz, status=BusinessStatus.APPROVED)
        await record_audit_event(
            self.db,
            action="business.approved",
            resource_type="business",
            resource_id=str(biz.id),
            actor_id=admin.id,
            actor_role=admin.role,
        )
        return await self.businesses.get_by_id_with_relations(biz.id)

    async def suspend(self, *, admin: User, business_id: uuid.UUID) -> Business:
        biz = await self.admin_get(business_id)
        biz = await self.businesses.update(biz, status=BusinessStatus.SUSPENDED)
        await record_audit_event(
            self.db,
            action="business.suspended",
            resource_type="business",
            resource_id=str(biz.id),
            actor_id=admin.id,
            actor_role=admin.role,
        )
        return await self.businesses.get_by_id_with_relations(biz.id)
