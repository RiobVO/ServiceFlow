# Changelog

Все заметные изменения в проекте документируются в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
а версии соответствуют [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- RFC 7807 Problem Details как единый формат ошибок (`application/problem+json`).
- Структурное логирование через structlog + сквозной `X-Request-ID` middleware.
- argon2id-хеширование API-ключей, prefix/last4-индексация, ротация ключей
  (`POST /api/v1/users/me/api-key/rotate`, админский вариант).
- Security headers middleware (CSP, X-Frame-Options, HSTS в prod и др.).
- SecretStr + валидация настроек при старте (длина `ADMIN_BOOTSTRAP_KEY`,
  формат DSN, запрет `CORS_ORIGINS=*` в prod).
- Rate limiting (slowapi) на чувствительные эндпоинты.
- Repository + Unit of Work; чистый доменный FSM в `app/domain`.
- `/api/v1` префикс, pagination envelope `Page[T]`, ETag + If-Match.
- Обогащённый OpenAPI: tags, operation_id, summary, responses с ProblemDetails.
- `/health/live` и `/health/ready` (k8s-style probes).
- Prometheus `/metrics` + бизнес-счётчики; опциональный OpenTelemetry (OTLP).
- Составные индексы и частичный индекс очереди; pool tuning (pre-ping, recycle).
- Idempotency-Key для `POST /api/v1/requests`.
- Outbox pattern + arq-воркер + Redis в docker-compose.
- Пирамида тестов: unit + integration (testcontainers) + contract (schemathesis).
- CI: ruff, ruff format, mypy --strict, pytest + coverage ≥ 85, trivy-scan docker образа.
- Multi-stage Dockerfile, non-root пользователь, HEALTHCHECK, tini init, `.dockerignore`.

### Changed
- Миграция с устаревшего `@app.on_event("startup")` на `lifespan`.
- Сервисы возвращают DTO через `Page.of(...)` вместо голых ORM-списков.

### Removed
- Колонка `api_key` (plaintext) — заменена на `api_key_prefix/last4/hash`.
- Устаревший `request_log_service` (функции в `RequestService`).
