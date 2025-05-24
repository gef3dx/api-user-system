from starlette.testclient import TestClient


def test_get_current_user_info(client: TestClient, test_user, auth_headers):
    """Тест получения информации о текущем пользователе"""
    response = client.get("/api/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


def test_get_current_user_unauthorized(client: TestClient):
    """Тест получения информации без авторизации"""
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_update_current_user(client: TestClient, test_user, auth_headers):
    """Тест обновления данных текущего пользователя"""
    update_data = {"email": "updated@example.com"}

    response = client.put("/api/users/me", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"


async def test_update_user_duplicate_email(
    client: TestClient, test_user, auth_headers, db_session
):
    """Тест обновления email на уже существующий"""
    # Создаем другого пользователя
    from app.models.user import User
    from app.core.security import get_password_hash

    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    update_data = {"email": "other@example.com"}

    response = client.put("/api/users/me", json=update_data, headers=auth_headers)
    assert response.status_code == 400


def test_get_users_as_superuser(client: TestClient, admin_headers):
    """Тест получения списка пользователей суперпользователем"""
    response = client.get("/api/users/", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_users_as_regular_user(client: TestClient, auth_headers):
    """Тест получения списка пользователей обычным пользователем"""
    response = client.get("/api/users/", headers=auth_headers)
    assert response.status_code == 403


def test_deactivate_user_as_superuser(client: TestClient, test_user, admin_headers):
    """Тест деактивации пользователя суперпользователем"""
    response = client.patch(
        f"/api/users/{test_user.id}/deactivate", headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


def test_deactivate_self(client: TestClient, test_superuser, admin_headers):
    """Тест попытки деактивировать себя"""
    response = client.patch(
        f"/api/users/{test_superuser.id}/deactivate", headers=admin_headers
    )
    assert response.status_code == 400
