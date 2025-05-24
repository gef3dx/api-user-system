from app.repositories.base import (
    BaseRepository,
    CRUDRepository,
    MultiCollectionRepository,
)
from app.repositories.user import UserRepository, ProfileRepository


class RepositoryManager(MultiCollectionRepository):
    """Менеджер репозиториев для централизованного доступа"""

    def __init__(self):
        super().__init__()
        # Инициализация всех репозиториев
        self.add_repository("users", UserRepository())
        self.add_repository("profiles", ProfileRepository())

    # Свойства для удобного доступа к репозиториям
    @property
    def users(self) -> UserRepository:
        return self.get_repository("users")

    @property
    def profiles(self) -> ProfileRepository:
        return self.get_repository("profiles")


# Глобальный экземпляр менеджера репозиториев
repo_manager = RepositoryManager()


# Функция-зависимость для FastAPI
def get_repository_manager() -> RepositoryManager:
    """Получить менеджер репозиториев для использования в эндпоинтах"""
    return repo_manager
