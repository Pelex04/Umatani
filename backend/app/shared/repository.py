"""
Generic repository base class.

Every module's repository extends this for standard CRUD, keeping
data-access concerns out of services and routers. Using the repository
pattern here means swapping persistence (e.g. adding a cache layer, or
extracting a module into its own service later) doesn't ripple into
business logic.
"""
import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing standard CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: uuid.UUID) -> ModelType | None:
        return await self.session.get(self.model, record_id)

    async def list(
        self, *, offset: int = 0, limit: int = 50, **filters: Any
    ) -> Sequence[ModelType]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **data: Any) -> ModelType:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **data: Any) -> ModelType:
        for field, value in data.items():
            setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
        await self.session.flush()
