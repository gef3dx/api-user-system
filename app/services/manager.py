from app.services.user_service import UserService
from app.services.profile_service import ProfileService
from app.services.auth_service import AuthService
from app.repositories import get_repository_manager


class ServiceManager:
    """Менеджер сервисов для централизованного управления"""

    def __init__(self):
        # Получаем менеджер репозиториев
        self.repo_manager = get_repository_manager()

        # Инициализируем сервисы
        self._user_service = UserService(self.repo_manager.users)
        self._profile_service = ProfileService(self.repo_manager.profiles)
        self._auth_service = AuthService(self._user_service)

    @property
    def users(self) -> UserService:
        """Сервис пользователей"""
        return self._user_service

    @property
    def profiles(self) -> ProfileService:
        """Сервис профилей"""
        return self._profile_service

    @property
    def auth(self) -> AuthService:
        """Сервис аутентификации"""
        return self._auth_service


# Глобальный экземпляр менеджера сервисов
service_manager = ServiceManager()


# Функция-зависимость для FastAPI
def get_service_manager() -> ServiceManager:
    """Получить менеджер сервисов для использования в эндпоинтах"""
    return service_manager