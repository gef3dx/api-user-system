from starlette.testclient import TestClient


def test_full_user_flow(client: TestClient):
    """Интеграционный тест полного пользовательского потока"""
    # 1. Регистрация
    user_data = {
        "email": "integration@example.com",
        "password": "password123",
        "profile": {"first_name": "Integration", "last_name": "Test"},
    }

    register_response = client.post("/api/auth/register", json=user_data)
    assert register_response.status_code == 200

    # 2. Авторизация
    login_data = {"username": "integration@example.com", "password": "password123"}

    login_response = client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Получение информации о пользователе
    user_info_response = client.get("/api/users/me", headers=headers)
    assert user_info_response.status_code == 200

    # 4. Получение профиля
    profile_response = client.get("/api/profiles/me", headers=headers)
    assert profile_response.status_code == 200

    # 5. Обновление профиля
    profile_update = {"bio": "Integration test bio"}

    profile_update_response = client.put(
        "/api/profiles/me", json=profile_update, headers=headers
    )
    assert profile_update_response.status_code == 200
    assert profile_update_response.json()["bio"] == "Integration test bio"


def test_unauthorized_access_to_protected_endpoints(client: TestClient):
    """Тест доступа к защищенным эндпоинтам без авторизации"""
    protected_endpoints = [
        "/api/users/me",
        "/api/profiles/me",
        "/api/profiles/search?first_name=test",
        "/api/users/",
        "/api/profiles/",
    ]

    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
