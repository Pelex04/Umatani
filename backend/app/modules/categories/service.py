"""
Categories service.

Slug uniqueness is enforced here, not at the DB level alone — if two
categories would generate the same slug (e.g. "Hair Styling" and "Hair
Styling!") we append a short suffix rather than failing opaquely.

Slug changes are blocked on update: changing a slug silently breaks any
external links, search engine indexes, or frontend routes that have
already been built from it.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import slugify
from app.shared.audit_service import record_audit_event


class CategoryError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    async def _unique_slug(self, base_slug: str) -> str:
        candidate = base_slug
        suffix = 1
        while await self.repo.get_by_slug(candidate) is not None:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate

    async def list_public(self) -> list[Category]:
        return await self.repo.list_active()

    async def get_public(self, category_id: uuid.UUID) -> Category:
        cat = await self.repo.get_by_id(category_id)
        if cat is None or not cat.is_active:
            raise CategoryError("Category not found")
        return cat

    async def list_admin(self) -> list[Category]:
        return await self.repo.list_all()

    async def get_admin(self, category_id: uuid.UUID) -> Category:
        cat = await self.repo.get_by_id(category_id)
        if cat is None:
            raise CategoryError("Category not found")
        return cat

    async def create(
        self,
        *,
        admin: User,
        name: str,
        description: str | None,
        icon_url: str | None,
        display_order: int,
    ) -> Category:
        existing = await self.repo.get_by_name(name)
        if existing is not None:
            raise CategoryError(f"A category named '{name}' already exists")

        slug = await self._unique_slug(slugify(name))

        cat = await self.repo.create(
            name=name,
            slug=slug,
            description=description,
            icon_url=icon_url,
            display_order=display_order,
            is_active=True,
        )
        await record_audit_event(
            self.db,
            action="category.created",
            resource_type="category",
            resource_id=str(cat.id),
            actor_id=admin.id,
            actor_role=admin.role,
            metadata={"name": name, "slug": slug},
        )
        return cat

    async def update(
        self,
        *,
        admin: User,
        category_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        icon_url: str | None = None,
        display_order: int | None = None,
        is_active: bool | None = None,
    ) -> Category:
        cat = await self.get_admin(category_id)

        if name is not None and name != cat.name:
            existing = await self.repo.get_by_name(name)
            if existing is not None and existing.id != cat.id:
                raise CategoryError(f"A category named '{name}' already exists")

        updates: dict = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if icon_url is not None:
            updates["icon_url"] = icon_url
        if display_order is not None:
            updates["display_order"] = display_order
        if is_active is not None:
            updates["is_active"] = is_active

        if updates:
            cat = await self.repo.update(cat, **updates)
            await record_audit_event(
                self.db,
                action="category.updated",
                resource_type="category",
                resource_id=str(cat.id),
                actor_id=admin.id,
                actor_role=admin.role,
                metadata=updates,
            )
        return cat
