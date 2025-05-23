from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Profile
from app.schemas.user import ProfileResponse, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Получение профиля текущего пользователя
    """
    # Загружаем пользователя с профилем
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == current_user.id)
    )
    result = await db.execute(stmt)
    user_with_profile = result.scalar_one()

    if not user_with_profile.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден"
        )
    return user_with_profile.profile


@router.put("/me", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновление профиля текущего пользователя
    """
    # Загружаем пользователя с профилем
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == current_user.id)
    )
    result = await db.execute(stmt)
    user_with_profile = result.scalar_one()

    # Проверка существования профиля
    if not user_with_profile.profile:
        # Создаем профиль если его нет
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    else:
        profile = user_with_profile.profile

    # Обновление полей профиля
    if profile_update.first_name is not None:
        profile.first_name = profile_update.first_name

    if profile_update.last_name is not None:
        profile.last_name = profile_update.last_name

    if profile_update.bio is not None:
        profile.bio = profile_update.bio

    if profile_update.avatar_url is not None:
        profile.avatar_url = profile_update.avatar_url

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile
