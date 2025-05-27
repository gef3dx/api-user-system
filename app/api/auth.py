from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import Deps
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreate, deps: Deps = Depends()):
    """
    Регистрация нового пользователя
    """
    try:
        user = await deps.services.auth.register_user(deps.db, user_in)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        deps: Deps = Depends()
):
    """
    Авторизация пользователя и получение токена
    """
    try:
        token = await deps.services.auth.login_user(
            deps.db, form_data.username, form_data.password
        )
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при авторизации"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        current_user: User = Depends(get_current_user),
        deps: Deps = Depends()
):
    """
    Обновление токена доступа
    """
    try:
        token = await deps.services.auth.refresh_token(deps.db, current_user)
        return token
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении токена"
        )


@router.post("/logout")
async def logout_user(
        current_user: User = Depends(get_current_user),
        deps: Deps = Depends()
):
    """
    Выход пользователя из системы
    """
    try:
        result = await deps.services.auth.logout_user(current_user)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выходе из системы"
        )


@router.post("/change-password")
async def change_password(
        old_password: str,
        new_password: str,
        current_user: User = Depends(get_current_user),
        deps: Deps = Depends()
):
    """
    Смена пароля пользователя
    """
    try:
        success = await deps.services.auth.change_password(
            deps.db, current_user, old_password, new_password
        )

        if success:
            return {"message": "Пароль успешно изменен"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось изменить пароль"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при смене пароля"
        )