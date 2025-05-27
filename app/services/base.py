from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(ABC, Generic[ModelType, RepositoryType]):
    """Базовый класс для сервисов"""

    def __init__(self, repository: RepositoryType):
        self.repository = repository

    @abstractmethod
    async def get_by_id(
        self, db: AsyncSession, id: Any
    ) -> Optional[ModelType]:
        """Получить объект по ID"""
        pass

    @abstractmethod
    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Получить список объектов"""
        pass

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        obj_in: Any
    ) -> ModelType:
        """Создать новый объект"""
        pass

    @abstractmethod
    async def update(
        self,
        db: AsyncSession,
        id: Any,
        obj_in: Any
    ) -> Optional[ModelType]:
        """Обновить объект"""
        pass

    @abstractmethod
    async def delete(
        self,
        db: AsyncSession,
        id: Any
    ) -> bool:
        """Удалить объект"""
        pass


class CRUDService(BaseService[ModelType, RepositoryType]):
    """Базовый CRUD сервис с реализацией основных операций"""

    async def get_by_id(
        self, db: AsyncSession, id: Any
    ) -> Optional[ModelType]:
        """Получить объект по ID"""
        return await self.repository.get_by_id(db, id)

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Получить список объектов с пагинацией"""
        return await self.repository.get_multi(db, skip=skip, limit=limit)

    async def create(
        self,
        db: AsyncSession,
        obj_in: Any
    ) -> ModelType:
        """Создать новый объект"""
        return await self.repository.create(db, obj_in=obj_in)

    async def update(
        self,
        db: AsyncSession,
        id: Any,
        obj_in: Any
    ) -> Optional[ModelType]:
        """Обновить объект"""
        db_obj = await self.repository.get_by_id(db, id)
        if not db_obj:
            return None
        return await self.repository.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete(
        self,
        db: AsyncSession,
        id: Any
    ) -> bool:
        """Удалить объект"""
        db_obj = await self.repository.remove(db, id=id)
        return db_obj is not None