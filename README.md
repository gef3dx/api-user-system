# Система авторизации и регистрации пользователей на FastAPI

Проект представляет собой API для авторизации, регистрации и управления профилями пользователей, построенный на FastAPI с использованием PostgreSQL в качестве базы данных и Alembic для миграций.

## Технологический стек

- **FastAPI**: Веб-фреймворк для создания API
- **SQLAlchemy**: ORM для работы с базой данных
- **PostgreSQL**: Реляционная база данных
- **Alembic**: Система миграций для SQLAlchemy
- **JWT**: Система аутентификации на основе токенов
- **Pydantic**: Валидация данных и сериализация/десериализация

## Основные возможности

- Регистрация пользователей
- Аутентификация на основе JWT токенов
- Управление профилем пользователя
- Защищенные маршруты API
- Хэширование паролей

## Установка и запуск

### Предварительные требования

- Python 3.8+
- PostgreSQL

### Шаги по установке

1. **Клонирование репозитория**

```bash
git clone https://github.com/yourusername/fastapi-auth-profile.git
cd fastapi-auth-profile
```

2. **Создание виртуального окружения**

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. **Установка зависимостей**

```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**

Создайте файл `.env` в корне проекта и настройте следующие переменные:

```
DATABASE_URL=postgresql://postgres:password@localhost/auth_db
SECRET_KEY=your_secure_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. **Создание базы данных**

Создайте базу данных в PostgreSQL:

```sql
CREATE DATABASE auth_db;
```

6. **Применение миграций**

```bash
alembic upgrade head
```

7. **Запуск сервера**

```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

Документация API: http://localhost:8000/docs

## Структура проекта

```
project/
├── alembic/
│   ├── versions/
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── profiles.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── token.py
│   │   └── user.py
│   ├── __init__.py
│   └── main.py
├── .env
├── alembic.ini
├── requirements.txt
└── README.md
```
## Запуск тестов
```bash
pytest tests/ -v --tb=short
```

## API Endpoints

### Аутентификация

- **POST /api/auth/register**: Регистрация нового пользователя
- **POST /api/auth/login**: Вход пользователя и получение токена

### Пользователи

- **GET /api/users/me**: Получение информации о текущем пользователе
- **PUT /api/users/me**: Обновление данных текущего пользователя

### Профили

- **GET /api/profiles/me**: Получение профиля текущего пользователя
- **PUT /api/profiles/me**: Обновление профиля текущего пользователя