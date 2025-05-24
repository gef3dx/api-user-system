from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import RepositoryManager, get_repository_manager


class DependencyContainer:
    """Контейнер зависимостей для удобного использования в эндпоинтах"""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        repos: RepositoryManager = Depends(get_repository_manager),
    ):
        self.db = db
        self.repos = repos


# Alias для удобства использования
Deps = DependencyContainer
