import pytest
from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    """Тест успешной регистрации пользователя"""
    user_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "profile": {"first_name": "New", "last_name": "User", "bio": "New user bio"},
    }

    response = client.post("/api/auth/register", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["is_active"] is True
    assert "id" in data
    assert data["profile"]["first_name"] == "New"


def test_register_duplicate_email(client: TestClient, test_user):
    """Тест регистрации с существующим email"""
    user_data = {"email": test_user.email, "password": "password123"}

    response = client.post("/api/auth/register", json=user_data)

    assert response.status_code == 400
    assert "Email уже зарегистрирован" in response.json()["detail"]


def test_register_invalid_email(client: TestClient):
    """Тест регистрации с некорректным email"""
    user_data = {"email": "invalid-email", "password": "password123"}

    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 422


def test_register_short_password(client: TestClient):
    """Тест регистрации с коротким паролем"""
    user_data = {"email": "test@example.com", "password": "123"}

    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 422


def test_login_success(client: TestClient, test_user):
    """Тест успешной авторизации"""
    form_data = {"username": test_user.email, "password": "testpassword123"}

    response = client.post("/api/auth/login", data=form_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user):
    """Тест авторизации с неверным паролем"""
    form_data = {"username": test_user.email, "password": "wrongpassword"}

    response = client.post("/api/auth/login", data=form_data)

    assert response.status_code == 401
    assert "Неверный email или пароль" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Тест авторизации несуществующего пользователя"""
    form_data = {"username": "nonexistent@example.com", "password": "password123"}

    response = client.post("/api/auth/login", data=form_data)

    assert response.status_code == 401
