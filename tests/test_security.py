from app.core.security import verify_password, get_password_hash, create_access_token
from jose import jwt
from app.core.config import settings


def test_password_hashing():
    """Тест хеширования и проверки пароля"""
    password = "testpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Тест создания JWT токена"""
    data = {"sub": "test@example.com", "user_id": 1}
    token = create_access_token(data)

    assert token is not None

    # Декодируем токен для проверки
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "test@example.com"
    assert payload["user_id"] == 1
    assert "exp" in payload
