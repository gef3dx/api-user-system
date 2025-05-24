from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import Deps
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
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Обновление данных текущего пользователя
    """
    # Проверка email на уникальность если он был изменен
    if user_update.email and user_update.email != current_user.email:
        existing_user = await deps.repos.users.get_by_email(deps.db, user_update.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован в системе",
            )

    # Подготовка данных для обновления
    update_data = user_update.dict(exclude_unset=True)

    # Хеширование пароля если он был предоставлен
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    # Обновление пользователя через репозиторий
    updated_user = await deps.repos.users.update(
        deps.db, db_obj=current_user, obj_in=update_data
    )

    # Получение обновленного пользователя с профилем
    return await deps.repos.users.get_by_id_with_profile(deps.db, updated_user.id)


@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Получение списка пользователей (только для суперпользователей)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа"
        )

    if active_only:
        users = await deps.repos.users.get_active_users(deps.db, skip=skip, limit=limit)
    else:
        users = await deps.repos.users.get_multi(deps.db, skip=skip, limit=limit)

    return users


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Деактивация пользователя (только для суперпользователей)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа"
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать свою учетную запись",
        )

    user = await deps.repos.users.deactivate_user(deps.db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    return user
