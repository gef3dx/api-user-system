from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import CRUDService
from app.repositories.user import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService(CRUDService[User, UserRepository]):
    """Сервис для работы с пользователями"""

    def __init__(self, repository: UserRepository):
        super().__init__(repository)

    async def get_by_email(
            self, db: AsyncSession, email: str
    ) -> Optional[User]:
        """Получить пользователя по email"""
        return await self.repository.get_by_email(db, email)

    async def get_by_id_with_profile(
            self, db: AsyncSession, user_id: int
    ) -> Optional[User]:
        """Получить пользователя с профилем"""
        return await self.repository.get_by_id_with_profile(db, user_id)

    async def create_user(
            self, db: AsyncSession, user_in: UserCreate
    ) -> User:
        """Создать нового пользователя с валидацией"""
        # Проверка существования пользователя
        existing_user = await self.repository.get_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован в системе"
            )

        # Хеширование пароля
        hashed_password = get_password_hash(user_in.password)

        # Создание пользователя через репозиторий
        return await self.repository.create_user(db, user_in, hashed_password)

    async def authenticate_user(
            self, db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """Аутентификация пользователя"""
        user = await self.repository.get_by_email(db, email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    async def update_user(
            self, db: AsyncSession, user_id: int, user_update: UserUpdate
    ) -> Optional[User]:
        """Обновить данные пользователя с валидацией"""
        db_user = await self.repository.get_by_id(db, user_id)
        if not db_user:
            return None

        # Проверка email на уникальность
        if user_update.email and user_update.email != db_user.email:
            existing_user = await self.repository.get_by_email(db, user_update.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже зарегистрирован в системе"
                )

        # Подготовка данных для обновления
        update_data = user_update.dict(exclude_unset=True)

        # Хеширование пароля если он был предоставлен
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        # Обновление через репозиторий
        return await self.repository.update(db, db_obj=db_user, obj_in=update_data)

    async def deactivate_user(
            self, db: AsyncSession, user_id: int, current_user_id: int
    ) -> Optional[User]:
        """Деактивировать пользователя"""
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя деактивировать свою учетную запись"
            )

        return await self.repository.deactivate_user(db, user_id)

    async def get_active_users(
            self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Получить список активных пользователей"""
        return await self.repository.get_active_users(db, skip=skip, limit=limit)

    async def check_superuser_permissions(self, user: User) -> bool:
        """Проверить права суперпользователя"""
        return user.is_superuser

    async def validate_user_access(
            self, user: User, target_user_id: Optional[int] = None
    ) -> bool:
        """Валидация доступа пользователя к ресурсу"""
        # Суперпользователь имеет доступ ко всему
        if user.is_superuser:
            return True

        # Пользователь имеет доступ только к своим данным
        if target_user_id and user.id != target_user_id:
            return False

        return True