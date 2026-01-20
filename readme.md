# ServiceFlow

ServiceFlow — backend-сервис для управления внутренними заявками и тикетами.
Production-style проект, реализованный на FastAPI, PostgreSQL и Docker.

Система предназначена для внутреннего использования в компаниях:
IT-поддержка, helpdesk, HR-заявки и операционные сервисные процессы.
Проект демонстрирует чистую backend-архитектуру с ролевой моделью,
бизнес-логикой, миграциями базы данных и контейнеризацией.

## Назначение проекта

ServiceFlow может использоваться как:
- внутренний IT / HelpDesk сервис
- backend для HR-заявок
- система обработки операционных запросов
- backend-ядро для Telegram-бота или web-панели

## Возможности

- создание и управление сервисными заявками
- бизнес-логика статусов заявок: NEW → IN_PROGRESS → DONE / CANCELED
- ролевая модель доступа:
  - ADMIN — полный доступ
  - AGENT — обработка заявок
  - EMPLOYEE — создание и просмотр своих заявок
- авторизация по API-ключам
- аудит и логирование действий по заявкам
- UUID / public_id для безопасной работы с идентификаторами
- PostgreSQL с миграциями Alembic
- поддержка Docker и Docker Compose
- seed-скрипт для начальной инициализации данных
- автоматические тесты

## Технологический стек

- Python 3
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Docker / Docker Compose
- Pytest

## Структура проекта

- app/routers — HTTP-эндпоинты API
- app/schemas — Pydantic-схемы
- app/models — ORM-модели SQLAlchemy
- app/services — бизнес-логика
- app/core — конфигурация, безопасность, зависимости
- alembic — миграции базы данных
- tests — автоматические тесты

## Установка и запуск (Docker)

Требования:
- Docker
- Docker Compose

1. Клонирование репозитория

   git clone https://github.com/RiobVO/ServiceFlow.git
   cd ServiceFlow

2. Создание файла окружения

   copy .env.example .env

3. Запуск приложения

   docker compose up --build

4. Применение миграций (при необходимости)

   docker compose exec backend alembic upgrade head

После запуска:
- API доступно по адресу: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Переменные окружения

Переменные окружения хранятся в файле .env (не коммитится в репозиторий).

Основные переменные:
- DATABASE_URL_POSTGRES — строка подключения к PostgreSQL
- API_KEY — ключ доступа к API
- ADMIN_BOOTSTRAP_KEY — ключ для первоначального создания администратора

Актуальные примеры смотрите в файле .env.example.

## Пример использования API

Создание заявки:

POST /requests  
X-API-Key: EMPLOYEE_API_KEY

Тело запроса:
{
  "title": "Не работает VPN",
  "description": "Соединение обрывается каждые 5 минут"
}

Изменение статуса заявки:

PATCH /requests/{id}/status  
X-API-Key: AGENT_API_KEY

Тело запроса:
{
  "status": "IN_PROGRESS"
}

## Тестирование

Запуск тестов внутри контейнера:

docker compose exec backend pytest

## План развития

- единый обработчик ошибок
- healthcheck с проверкой доступности базы данных
- хэширование API-ключей и endpoint для их сброса
- расширенное аудит-логирование
- ERD и диаграммы бизнес-процессов
- административная панель или интеграция с Telegram-ботом


