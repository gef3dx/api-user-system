from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC, Generic[ModelType]):
    """Абстрактный базовый репозиторий"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        pass

    @abstractmethod
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        pass

    @abstractmethod
    async def create(
        self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        pass

    @abstractmethod
    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        pass

    @abstractmethod
    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        pass


class CRUDRepository(BaseRepository[ModelType]):
    """Базовый CRUD репозиторий с реализацией основных операций"""

    def __init__(self, model: Type[ModelType]):
        super().__init__(model)

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Получить объект по ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Получить список объектов с пагинацией"""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, *, obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        """Создать новый объект"""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = self.model(
                **obj_in.dict() if hasattr(obj_in, "dict") else obj_in.__dict__
            )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        """Обновить существующий объект"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = (
                obj_in.dict(exclude_unset=True)
                if hasattr(obj_in, "dict")
                else obj_in.__dict__
            )

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """Удалить объект по ID"""
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

    async def get_by_field(
        self, db: AsyncSession, field_name: str, field_value: Any
    ) -> Optional[ModelType]:
        """Получить объект по значению поля"""
        stmt = select(self.model).where(getattr(self.model, field_name) == field_value)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_field(
        self, db: AsyncSession, field_name: str, field_value: Any
    ) -> List[ModelType]:
        """Получить список объектов по значению поля"""
        stmt = select(self.model).where(getattr(self.model, field_name) == field_value)
        result = await db.execute(stmt)
        return result.scalars().all()


class MultiCollectionRepository:
    """Репозиторий для работы с несколькими коллекциями"""

    def __init__(self):
        self._repositories: Dict[str, BaseRepository] = {}

    def add_repository(self, name: str, repository: BaseRepository) -> None:
        """Добавить репозиторий в коллекцию"""
        self._repositories[name] = repository

    def get_repository(self, name: str) -> BaseRepository:
        """Получить репозиторий по имени"""
        if name not in self._repositories:
            raise ValueError(f"Repository '{name}' not found")
        return self._repositories[name]

    def __getattr__(self, name: str) -> BaseRepository:
        """Позволяет обращаться к репозиториям через атрибуты"""
        try:
            return self.get_repository(name)
        except ValueError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
