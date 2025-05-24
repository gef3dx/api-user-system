from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import Deps
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreate, deps: Deps = Depends()):
    """
    Регистрация нового пользователя
    """
    # Проверка существования пользователя с таким email
    db_user = await deps.repos.users.get_by_email(deps.db, user_in.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован в системе",
        )

    # Создание пользователя с профилем
    hashed_password = get_password_hash(user_in.password)
    db_user = await deps.repos.users.create_user(deps.db, user_in, hashed_password)

    return db_user


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), deps: Deps = Depends()
):
    """
    Авторизация пользователя и получение токена
    """
    # Поиск пользователя по email
    user = await deps.repos.users.get_by_email(deps.db, form_data.username)

    # Проверка пароля и активности пользователя
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Учетная запись неактивна"
        )

    # Создание токена доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
