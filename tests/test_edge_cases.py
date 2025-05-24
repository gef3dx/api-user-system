from starlette.testclient import TestClient


def test_update_profile_with_empty_data(client: TestClient, auth_headers):
    """Тест обновления профиля пустыми данными"""
    response = client.put("/api/profiles/me", json={}, headers=auth_headers)
    assert response.status_code == 200


def test_search_profiles_with_pagination(client: TestClient, auth_headers):
    """Тест поиска профилей с пагинацией"""
    response = client.get(
        "/api/profiles/search?first_name=Test&skip=0&limit=10", headers=auth_headers
    )
    assert response.status_code == 200


def test_login_with_inactive_user(client: TestClient, db_session):
    """Тест авторизации неактивного пользователя"""
    from app.models.user import User
    from app.core.security import get_password_hash

    # Создаем неактивного пользователя
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()

    form_data = {"username": "inactive@example.com", "password": "password123"}

    response = client.post("/api/auth/login", data=form_data)
    assert response.status_code == 403
    assert "неактивна" in response.json()["detail"]
