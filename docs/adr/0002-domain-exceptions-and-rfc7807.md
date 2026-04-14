# 0002. Доменные исключения + RFC 7807 Problem Details

- Статус: Accepted
- Дата: 2026-04-18

## Контекст

До этого сервисы и policies кидали микс `ValueError` и `HTTPException`.
Роутеры вручную перехватывали `ValueError` и мапили на 400.
В результате сервис зависит от HTTP-слоя, и часть логики тестируется
только через TestClient.

## Рассмотренные варианты

- Оставить `HTTPException` на всех слоях. Просто, но сервисы прибиты к FastAPI.
- Использовать `ValueError` с кодовыми строками. Нестрогое API, каждый роут парсит.
- **DomainError**-иерархия + маппер в RFC 7807.

## Решение

Ввести `DomainError` и потомков (`PermissionDenied`, `NotFoundError`,
`ConflictError`, специфичные бизнес-ошибки). Один глобальный хендлер
возвращает `application/problem+json` с полями `type/title/status/detail/instance/code/request_id`.

## Последствия

- (+) Сервисы юнит-тестируются без FastAPI.
- (+) Единый формат ошибок для клиентов.
- (+) Новые ошибки требуют явно задать `code`, `http_status`.
- (−) Break-change в формате ошибок — фронт/интеграции надо обновить
  (отражено в CHANGELOG).
