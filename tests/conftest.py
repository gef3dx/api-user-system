import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from typing import AsyncGenerator, Generator

from app.main import app
from app.core.database import get_db, Base
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, Profile
from app.repositories import get_repository_manager


# Настройка тестовой базы данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает тестовую сессию базы данных"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Создает тестовый клиент FastAPI"""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Создает тестового пользователя"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Создаем профиль
    profile = Profile(
        user_id=user.id, first_name="Test", last_name="User", bio="Test bio"
    )
    db_session.add(profile)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Создает тестового суперпользователя"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Создает заголовки авторизации для тестового пользователя"""
    access_token = create_access_token(
        data={"sub": test_user.email, "user_id": test_user.id}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(test_superuser: User) -> dict:
    """Создает заголовки авторизации для суперпользователя"""
    access_token = create_access_token(
        data={"sub": test_superuser.email, "user_id": test_superuser.id}
    )
    return {"Authorization": f"Bearer {access_token}"}
