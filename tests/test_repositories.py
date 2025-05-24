import pytest
import pytest_asyncio

from app.repositories.user import UserRepository, ProfileRepository
from app.schemas.user import UserCreate, ProfileCreate


@pytest_asyncio.fixture
async def user_repo():
    return UserRepository()


@pytest_asyncio.fixture
async def profile_repo():
    return ProfileRepository()


async def test_user_repository_create_user(db_session, user_repo):
    """Тест создания пользователя через репозиторий"""
    user_data = UserCreate(
        email="repo_test@example.com",
        password="password123",
        profile=ProfileCreate(first_name="Repo", last_name="Test"),
    )

    user = await user_repo.create_user(db_session, user_data, "hashed_password")

    assert user.email == "repo_test@example.com"
    assert user.profile is not None
    assert user.profile.first_name == "Repo"


async def test_user_repository_get_by_email(db_session, user_repo, test_user):
    """Тест получения пользователя по email"""
    user = await user_repo.get_by_email(db_session, test_user.email)

    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


async def test_user_repository_get_active_users(db_session, user_repo, test_user):
    """Тест получения активных пользователей"""
    users = await user_repo.get_active_users(db_session)

    assert len(users) >= 1
    assert all(user.is_active for user in users)


async def test_user_repository_deactivate_user(db_session, user_repo, test_user):
    """Тест деактивации пользователя"""
    deactivated_user = await user_repo.deactivate_user(db_session, test_user.id)

    assert deactivated_user is not None
    assert deactivated_user.is_active is False


async def test_profile_repository_get_by_user_id(db_session, profile_repo, test_user):
    """Тест получения профиля по ID пользователя"""
    profile = await profile_repo.get_by_user_id(db_session, test_user.id)

    assert profile is not None
    assert profile.user_id == test_user.id


async def test_profile_repository_update_profile(db_session, profile_repo, test_user):
    """Тест обновления профиля"""
    profile = await profile_repo.get_by_user_id(db_session, test_user.id)

    updated_profile = await profile_repo.update_profile(
        db_session, profile, first_name="Updated", bio="Updated bio"
    )

    assert updated_profile.first_name == "Updated"
    assert updated_profile.bio == "Updated bio"


async def test_profile_repository_search_by_name(db_session, profile_repo):
    """Тест поиска профилей по имени"""
    profiles = await profile_repo.get_profiles_by_name(db_session, first_name="Test")

    assert len(profiles) >= 1
    assert all(
        "Test" in profile.first_name for profile in profiles if profile.first_name
    )
