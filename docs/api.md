# API Cookbook

Сценарии ключевых операций. Полный контракт — в Swagger UI (`/docs` в dev/staging) или
[OpenAPI JSON](http://localhost:8000/openapi.json).

## Конвенции

- Все доменные эндпоинты — под `/api/v1/...`.
- Аутентификация — `X-API-Key: <ключ>`.
- Ошибки — `application/problem+json` (RFC 7807) с полями `type, title, status, detail, instance, code, request_id`.
- Идемпотентность `POST` — заголовок `Idempotency-Key: <uuid>`.
- Optimistic concurrency на `PATCH` — `If-Match: <ETag>`.
- Каждый ответ содержит `X-Request-ID` для корреляции с логами.

---

## 1. Bootstrap первого администратора

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Key: $ADMIN_BOOTSTRAP_KEY" \
  -d '{"full_name":"Admin","email":"admin@example.com"}'
```

Сохрани `api_key` из ответа — **он показывается один раз**.

## 2. Создание пользователей (только ADMIN)

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "X-API-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Support Agent","email":"agent@example.com"}'
```

## 3. Создание заявки (идемпотентно)

```bash
curl -X POST http://localhost:8000/api/v1/requests \
  -H "X-API-Key: $EMPLOYEE_KEY" \
  -H "Idempotency-Key: 7b3c7f6e-...-uuid" \
  -H "Content-Type: application/json" \
  -d '{"title":"Ноутбук не включается","description":"Чёрный экран"}'
```

Повтор с тем же ключом и телом → сохранённый ответ. Тот же ключ, другое тело → `409 idempotency_key_conflict`.

## 4. Смена статуса с optimistic lock

```bash
# 1) читаем текущую заявку — получаем ETag
curl -i -H "X-API-Key: $ADMIN_KEY" http://localhost:8000/api/v1/requests/42
# ETag: "abc123..."

# 2) меняем статус, передавая If-Match
curl -X PATCH http://localhost:8000/api/v1/requests/42/status \
  -H "X-API-Key: $ADMIN_KEY" \
  -H 'If-Match: "abc123..."' \
  -H "Content-Type: application/json" \
  -d '{"status":"IN_PROGRESS","assignee_id":5}'
```

Если с момента `GET` кто-то уже изменил заявку — `412 optimistic_lock_failed`.

## 5. Ротация собственного API-ключа

```bash
curl -X POST http://localhost:8000/api/v1/users/me/api-key/rotate \
  -H "X-API-Key: $MY_KEY"
# { "api_key": "<новый сырой>", "api_key_last4": "..." }
```

Старый ключ немедленно перестаёт работать. Лимит: 3 ротации в час на пользователя.

## 6. Pagination

Все `GET`-списки возвращают envelope:

```json
{
  "items": [...],
  "total": 123,
  "limit": 50,
  "offset": 0,
  "has_next": true
}
```

## 7. Формат ошибок

```json
{
  "type": "https://serviceflow.local/errors/invalid_status_transition",
  "title": "Bad Request",
  "status": 400,
  "detail": "Переход NEW → DONE запрещён.",
  "instance": "/api/v1/requests/42/status",
  "code": "invalid_status_transition",
  "request_id": "2bc8b8d6682048eeab539a149da00210",
  "errors": {"from": "NEW", "to": "DONE"}
}
```
