from typing import Any, Dict, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload


class FilterMixin:
    """Миксин для добавления возможностей фильтрации"""

    async def filter_by(
        self, db: AsyncSession, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[Any]:
        """Фильтрация по множественным критериям"""
        stmt = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_by_text(
        self,
        db: AsyncSession,
        field_name: str,
        search_text: str,
        case_sensitive: bool = False,
    ) -> List[Any]:
        """Текстовый поиск по полю"""
        if not hasattr(self.model, field_name):
            return []

        field = getattr(self.model, field_name)

        if case_sensitive:
            stmt = select(self.model).where(field.like(f"%{search_text}%"))
        else:
            stmt = select(self.model).where(field.ilike(f"%{search_text}%"))

        result = await db.execute(stmt)
        return result.scalars().all()


class CountMixin:
    """Миксин для подсчета записей"""

    async def count_all(self, db: AsyncSession) -> int:
        """Подсчет всех записей"""
        stmt = select(func.count(self.model.id))
        result = await db.execute(stmt)
        return result.scalar()

    async def count_by_field(
        self, db: AsyncSession, field_name: str, field_value: Any
    ) -> int:
        """Подсчет записей по значению поля"""
        if not hasattr(self.model, field_name):
            return 0

        stmt = select(func.count(self.model.id)).where(
            getattr(self.model, field_name) == field_value
        )
        result = await db.execute(stmt)
        return result.scalar()


class SoftDeleteMixin:
    """Миксин для мягкого удаления (если модель поддерживает)"""

    async def soft_delete(self, db: AsyncSession, id: Any) -> Optional[Any]:
        """Мягкое удаление записи"""
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError("Model doesn't support soft delete")

        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db_obj.is_deleted = True
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def restore(self, db: AsyncSession, id: Any) -> Optional[Any]:
        """Восстановление удаленной записи"""
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError("Model doesn't support soft delete")

        stmt = select(self.model).where(
            and_(self.model.id == id, self.model.is_deleted == True)
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()

        if db_obj:
            db_obj.is_deleted = False
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj


class BulkOperationsMixin:
    """Миксин для массовых операций"""

    async def bulk_create(
        self, db: AsyncSession, objects_data: List[Dict[str, Any]]
    ) -> List[Any]:
        """Массовое создание объектов"""
        db_objects = [self.model(**obj_data) for obj_data in objects_data]
        db.add_all(db_objects)
        await db.commit()

        for obj in db_objects:
            await db.refresh(obj)

        return db_objects

    async def bulk_update(
        self, db: AsyncSession, ids: List[Any], update_data: Dict[str, Any]
    ) -> int:
        """Массовое обновление объектов"""
        stmt = update(self.model).where(self.model.id.in_(ids)).values(**update_data)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def bulk_delete(self, db: AsyncSession, ids: List[Any]) -> int:
        """Массовое удаление объектов"""
        stmt = delete(self.model).where(self.model.id.in_(ids))
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
