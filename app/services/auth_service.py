from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.core.security import create_access_token
from app.core.config import settings


class AuthService:
    """Сервис для аутентификации и авторизации"""

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def register_user(
            self, db: AsyncSession, user_in: UserCreate
    ) -> User:
        """Регистрация нового пользователя"""
        # Валидация данных
        await self._validate_registration_data(user_in)

        # Создание пользователя через сервис
        return await self.user_service.create_user(db, user_in)

    async def login_user(
            self, db: AsyncSession, email: str, password: str
    ) -> Token:
        """Аутентификация пользователя и создание токена"""
        # Аутентификация через сервис пользователей
        user = await self.user_service.authenticate_user(db, email, password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Создание токена доступа
        access_token = await self._create_user_token(user)

        return Token(access_token=access_token, token_type="bearer")

    async def refresh_token(
            self, db: AsyncSession, user: User
    ) -> Token:
        """Обновление токена доступа"""
        # Проверяем что пользователь все еще активен
        current_user = await self.user_service.get_by_id(db, user.id)

        if not current_user or not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь неактивен"
            )

        # Создание нового токена
        access_token = await self._create_user_token(current_user)

        return Token(access_token=access_token, token_type="bearer")

    async def validate_user_status(self, user: User) -> bool:
        """Проверка статуса пользователя"""
        return user.is_active

    async def check_user_permissions(
            self, user: User, required_permission: str
    ) -> bool:
        """Проверка прав доступа пользователя"""
        permission_map = {
            "superuser": user.is_superuser,
            "active": user.is_active,
        }

        return permission_map.get(required_permission, False)

    async def _validate_registration_data(self, user_in: UserCreate) -> None:
        """Валидация данных регистрации"""
        # Проверка надежности пароля
        if len(user_in.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать минимум 8 символов"
            )

        # Дополнительные проверки пароля
        if not any(c.isupper() for c in user_in.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать хотя бы одну заглавную букву"
            )

        if not any(c.islower() for c in user_in.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать хотя бы одну строчную букву"
            )

        if not any(c.isdigit() for c in user_in.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAB_REQUEST,
                detail="Пароль должен содержать хотя бы одну цифру"
            )

    async def _create_user_token(self, user: User) -> str:
        """Создание токена для пользователя"""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        return create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )

    async def logout_user(self, user: User) -> dict:
        """Выход пользователя из системы"""
        # В текущей реализации с JWT токенами мы не можем
        # отозвать токен на сервере, но можем вернуть
        # успешный ответ для клиента
        return {
            "message": "Успешный выход из системы",
            "user_id": user.id
        }

    async def change_password(
            self,
            db: AsyncSession,
            user: User,
            old_password: str,
            new_password: str
    ) -> bool:
        """Смена пароля пользователя"""
        # Проверка старого пароля
        from app.core.security import verify_password

        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный текущий пароль"
            )

        # Валидация нового пароля
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Новый пароль должен содержать минимум 8 символов"
            )

        # Обновление пароля через сервис пользователей
        from app.schemas.user import UserUpdate
        user_update = UserUpdate(password=new_password)

        updated_user = await self.user_service.update_user(
            db, user.id, user_update
        )

        return updated_user is not None