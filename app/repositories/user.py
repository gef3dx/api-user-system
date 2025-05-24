# app/repositories/user.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import CRUDRepository
from app.models.user import User, Profile
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(CRUDRepository[User]):
    """Репозиторий для работы с пользователями"""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return await self.get_by_field(db, "email", email)

    async def get_by_id_with_profile(self, db: AsyncSession, id: int) -> Optional[User]:
        """Получить пользователя с профилем по ID"""
        stmt = select(User).options(selectinload(User.profile)).where(User.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_with_profile(
        self, db: AsyncSession, email: str
    ) -> Optional[User]:
        """Получить пользователя с профилем по email"""
        stmt = (
            select(User).options(selectinload(User.profile)).where(User.email == email)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, db: AsyncSession, user_in: UserCreate, hashed_password: str
    ) -> User:
        """Создать пользователя с профилем"""
        # Создание пользователя
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # Создание профиля
        if user_in.profile:
            profile = Profile(
                user_id=db_user.id,
                first_name=user_in.profile.first_name,
                last_name=user_in.profile.last_name,
                bio=user_in.profile.bio,
                avatar_url=user_in.profile.avatar_url,
            )
        else:
            profile = Profile(user_id=db_user.id)

        db.add(profile)
        await db.commit()

        # Возвращаем пользователя с профилем
        return await self.get_by_id_with_profile(db, db_user.id)

    async def update_user(
        self, db: AsyncSession, db_user: User, user_update: UserUpdate
    ) -> User:
        """Обновить данные пользователя"""
        update_data = user_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)

        db.add(db_user)
        await db.commit()

        return await self.get_by_id_with_profile(db, db_user.id)

    async def get_active_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Получить список активных пользователей"""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Деактивировать пользователя"""
        db_user = await self.get_by_id(db, user_id)
        if db_user:
            db_user.is_active = False
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        return db_user


class ProfileRepository(CRUDRepository[Profile]):
    """Репозиторий для работы с профилями"""

    def __init__(self):
        super().__init__(Profile)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[Profile]:
        """Получить профиль по ID пользователя"""
        return await self.get_by_field(db, "user_id", user_id)

    async def create_profile(
        self, db: AsyncSession, user_id: int, **profile_data
    ) -> Profile:
        """Создать профиль для пользователя"""
        profile = Profile(user_id=user_id, **profile_data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def update_profile(
        self, db: AsyncSession, db_profile: Profile, **update_data
    ) -> Profile:
        """Обновить профиль"""
        for field, value in update_data.items():
            if hasattr(db_profile, field) and value is not None:
                setattr(db_profile, field, value)

        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
        return db_profile

    async def get_profiles_by_name(
        self, db: AsyncSession, first_name: str = None, last_name: str = None
    ) -> List[Profile]:
        """Поиск профилей по имени"""
        stmt = select(Profile)

        if first_name:
            stmt = stmt.where(Profile.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.where(Profile.last_name.ilike(f"%{last_name}%"))

        result = await db.execute(stmt)
        return result.scalars().all()
