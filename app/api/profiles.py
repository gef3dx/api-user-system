from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.dependencies import Deps
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import ProfileResponse, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Получение профиля текущего пользователя
    """
    profile = await deps.repos.profiles.get_by_user_id(deps.db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден"
        )

    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Обновление профиля текущего пользователя
    """
    # Поиск существующего профиля
    profile = await deps.repos.profiles.get_by_user_id(deps.db, current_user.id)

    if not profile:
        # Создаем профиль если его нет
        update_data = profile_update.dict(exclude_unset=True)
        profile = await deps.repos.profiles.create_profile(
            deps.db, current_user.id, **update_data
        )
    else:
        # Обновляем существующий профиль
        update_data = profile_update.dict(exclude_unset=True)
        profile = await deps.repos.profiles.update_profile(
            deps.db, profile, **update_data
        )

    return profile


@router.get("/search", response_model=list[ProfileResponse])
async def search_profiles(
    first_name: Optional[str] = Query(None, description="Поиск по имени"),
    last_name: Optional[str] = Query(None, description="Поиск по фамилии"),
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(
        100, ge=1, le=1000, description="Максимальное количество записей"
    ),
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Поиск профилей по имени и фамилии
    """
    if not first_name and not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать хотя бы один параметр поиска",
        )

    profiles = await deps.repos.profiles.get_profiles_by_name(
        deps.db, first_name=first_name, last_name=last_name
    )

    # Применяем пагинацию
    return profiles[skip : skip + limit]


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Получение профиля пользователя по ID
    """
    profile = await deps.repos.profiles.get_by_user_id(deps.db, user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден"
        )

    return profile


@router.get("/", response_model=list[ProfileResponse])
async def get_all_profiles(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(
        100, ge=1, le=1000, description="Максимальное количество записей"
    ),
    current_user: User = Depends(get_current_user),
    deps: Deps = Depends(),
):
    """
    Получение списка всех профилей (только для суперпользователей)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа"
        )

    profiles = await deps.repos.profiles.get_multi(deps.db, skip=skip, limit=limit)
    return profiles
