from starlette.testclient import TestClient


def test_get_current_user_profile(client: TestClient, test_user, auth_headers):
    """Тест получения профиля текущего пользователя"""
    response = client.get("/api/profiles/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


def test_update_current_user_profile(client: TestClient, auth_headers):
    """Тест обновления профиля текущего пользователя"""
    update_data = {"first_name": "Updated", "last_name": "Name", "bio": "Updated bio"}

    response = client.put("/api/profiles/me", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["bio"] == "Updated bio"


def test_search_profiles_by_name(client: TestClient, auth_headers):
    """Тест поиска профилей по имени"""
    response = client.get("/api/profiles/search?first_name=Test", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["first_name"] == "Test"


def test_search_profiles_no_params(client: TestClient, auth_headers):
    """Тест поиска без параметров"""
    response = client.get("/api/profiles/search", headers=auth_headers)
    assert response.status_code == 400


def test_get_user_profile_by_id(client: TestClient, test_user, auth_headers):
    """Тест получения профиля пользователя по ID"""
    response = client.get(f"/api/profiles/{test_user.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id


def test_get_nonexistent_profile(client: TestClient, auth_headers):
    """Тест получения несуществующего профиля"""
    response = client.get("/api/profiles/99999", headers=auth_headers)
    assert response.status_code == 404


def test_get_all_profiles_as_superuser(client: TestClient, admin_headers):
    """Тест получения всех профилей суперпользователем"""
    response = client.get("/api/profiles/", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_all_profiles_as_regular_user(client: TestClient, auth_headers):
    """Тест получения всех профилей обычным пользователем"""
    response = client.get("/api/profiles/", headers=auth_headers)
    assert response.status_code == 403
