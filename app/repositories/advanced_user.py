from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.repositories.base import CRUDRepository
from app.repositories.mixins import FilterMixin, CountMixin, BulkOperationsMixin
from app.models.user import User, Profile


class AdvancedUserRepository(
    CRUDRepository[User], FilterMixin, CountMixin, BulkOperationsMixin
):
    """Расширенный репозиторий пользователей с дополнительными возможностями"""

    def __init__(self):
        super().__init__(User)

    async def get_users_with_profiles(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[User]:
        """Получить пользователей с профилями"""
        stmt = select(User).options(selectinload(User.profile))

        if not include_inactive:
            stmt = stmt.where(User.is_active == True)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_users(
        self, db: AsyncSession, search_query: str, search_fields: List[str] = None
    ) -> List[User]:
        """Поиск пользователей по нескольким полям"""
        if not search_fields:
            search_fields = ["email"]

        conditions = []

        for field_name in search_fields:
            if hasattr(User, field_name):
                field = getattr(User, field_name)
                conditions.append(field.ilike(f"%{search_query}%"))

        if not conditions:
            return []

        stmt = select(User).where(or_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_users_registered_in_period(
        self, db: AsyncSession, start_date: datetime, end_date: datetime
    ) -> List[User]:
        """Получить пользователей, зарегистрированных в определенный период"""
        stmt = select(User).where(
            and_(User.created_at >= start_date, User.created_at <= end_date)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_user_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        total_users = await self.count_all(db)
        active_users = await self.count_by_field(db, "is_active", True)
        superusers = await self.count_by_field(db, "is_superuser", True)

        # Пользователи, зарегистрированные за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users_stmt = select(func.count(User.id)).where(
            User.created_at >= thirty_days_ago
        )
        result = await db.execute(recent_users_stmt)
        recent_users = result.scalar()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "superusers": superusers,
            "recent_registrations": recent_users,
        }

    async def get_users_by_profile_criteria(
        self,
        db: AsyncSession,
        has_avatar: Optional[bool] = None,
        has_bio: Optional[bool] = None,
        first_name: Optional[str] = None,
    ) -> List[User]:
        """Поиск пользователей по критериям профиля"""
        stmt = select(User).options(selectinload(User.profile)).join(Profile)

        conditions = []

        if has_avatar is not None:
            if has_avatar:
                conditions.append(Profile.avatar_url.isnot(None))
                conditions.append(Profile.avatar_url != "")
            else:
                conditions.append(
                    or_(Profile.avatar_url.is_(None), Profile.avatar_url == "")
                )

        if has_bio is not None:
            if has_bio:
                conditions.append(Profile.bio.isnot(None))
                conditions.append(Profile.bio != "")
            else:
                conditions.append(or_(Profile.bio.is_(None), Profile.bio == ""))

        if first_name:
            conditions.append(Profile.first_name.ilike(f"%{first_name}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        return result.scalars().all()


# Пример использования расширенного репозитория в API
"""
# app/api/admin.py
from app.repositories.advanced_user import AdvancedUserRepository

@router.get("/statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends()
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Используем расширенный репозиторий
    advanced_repo = AdvancedUserRepository()
    stats = await advanced_repo.get_user_statistics(deps.db)

    return stats
"""
