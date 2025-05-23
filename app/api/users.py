from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновление данных текущего пользователя
    """
    # Проверка email на уникальность если он был изменен
    if user_update.email and user_update.email != current_user.email:
        stmt = select(User).where(User.email == user_update.email)
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован в системе",
            )
        current_user.email = user_update.email

    # Обновление пароля если он был предоставлен
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)

    db.add(current_user)
    await db.commit()

    # Загружаем обновленного пользователя с профилем
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == current_user.id)
    )
    result = await db.execute(stmt)
    updated_user = result.scalar_one()

    return updated_user
