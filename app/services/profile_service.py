from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import CRUDService
from app.repositories.user import ProfileRepository
from app.models.user import Profile
from app.schemas.user import ProfileUpdate


class ProfileService(CRUDService[Profile, ProfileRepository]):
    """Сервис для работы с профилями пользователей"""

    def __init__(self, repository: ProfileRepository):
        super().__init__(repository)

    async def get_by_user_id(
            self, db: AsyncSession, user_id: int
    ) -> Optional[Profile]:
        """Получить профиль по ID пользователя"""
        return await self.repository.get_by_user_id(db, user_id)

    async def get_or_create_profile(
            self, db: AsyncSession, user_id: int, **profile_data
    ) -> Profile:
        """Получить существующий профиль или создать новый"""
        profile = await self.repository.get_by_user_id(db, user_id)

        if not profile:
            profile = await self.repository.create_profile(
                db, user_id, **profile_data
            )

        return profile

    async def update_user_profile(
            self, db: AsyncSession, user_id: int, profile_update: ProfileUpdate
    ) -> Profile:
        """Обновить профиль пользователя"""
        profile = await self.repository.get_by_user_id(db, user_id)

        if not profile:
            # Создаем профиль если его нет
            update_data = profile_update.dict(exclude_unset=True)
            profile = await self.repository.create_profile(
                db, user_id, **update_data
            )
        else:
            # Обновляем существующий профиль
            update_data = profile_update.dict(exclude_unset=True)
            profile = await self.repository.update_profile(
                db, profile, **update_data
            )

        return profile

    async def search_profiles(
            self,
            db: AsyncSession,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[Profile]:
        """Поиск профилей по имени и фамилии"""
        if not first_name and not last_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Необходимо указать хотя бы один параметр поиска"
            )

        profiles = await self.repository.get_profiles_by_name(
            db, first_name=first_name, last_name=last_name
        )

        # Применяем пагинацию
        return profiles[skip:skip + limit]

    async def validate_profile_data(self, profile_data: dict) -> dict:
        """Валидация и очистка данных профиля"""
        # Удаляем пустые строки и None значения
        cleaned_data = {}

        for key, value in profile_data.items():
            if value is not None and value != "":
                # Обрезаем пробелы для строковых полей
                if isinstance(value, str):
                    cleaned_data[key] = value.strip()
                else:
                    cleaned_data[key] = value

        return cleaned_data

    async def get_profile_completion_status(
            self, db: AsyncSession, user_id: int
    ) -> dict:
        """Получить статус заполненности профиля"""
        profile = await self.repository.get_by_user_id(db, user_id)

        if not profile:
            return {
                "completion_percentage": 0,
                "missing_fields": ["first_name", "last_name", "bio", "avatar_url"],
                "completed_fields": []
            }

        total_fields = 4
        completed_fields = []
        missing_fields = []

        # Проверяем заполненность полей
        fields_to_check = ["first_name", "last_name", "bio", "avatar_url"]

        for field in fields_to_check:
            value = getattr(profile, field, None)
            if value and value.strip():
                completed_fields.append(field)
            else:
                missing_fields.append(field)

        completion_percentage = (len(completed_fields) / total_fields) * 100

        return {
            "completion_percentage": round(completion_percentage, 2),
            "missing_fields": missing_fields,
            "completed_fields": completed_fields
        }

    async def update_avatar(
            self,
            db: AsyncSession,
            user_id: int,
            avatar_url: str
    ) -> Profile:
        """Обновить аватар пользователя"""
        # Валидация URL (базовая)
        if not avatar_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный URL аватара"
            )

        profile = await self.get_or_create_profile(db, user_id)
        return await self.repository.update_profile(
            db, profile, avatar_url=avatar_url
        )

    async def delete_avatar(
            self, db: AsyncSession, user_id: int
    ) -> Profile:
        """Удалить аватар пользователя"""
        profile = await self.repository.get_by_user_id(db, user_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Профиль не найден"
            )

        return await self.repository.update_profile(
            db, profile, avatar_url=None
        )