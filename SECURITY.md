# Security Policy

## Surface

- Аутентификация по API-ключу (`X-API-Key`). Ключ хранится только как argon2id-хеш.
- Bootstrap первого администратора — через одноразовый `X-Bootstrap-Key`
  с валидацией минимальной длины 24 символа.
- Rate limiting: `POST /api/v1/users` 5/min/IP, `rotate` 3/hour/user.
- Security headers: CSP (`default-src 'none'`), `X-Frame-Options: DENY`,
  `Referrer-Policy`, HSTS (только prod+https).
- CORS: явный whitelist origins, `*` запрещён в prod.
- Единый формат ошибок RFC 7807 — детальные сообщения не раскрывают
  внутренности (`internal_server_error` без стектрейса в ответе).

## Что закрыто по архитектуре

- **Plaintext keys in DB** — невозможно: храним только argon2id-хеш.
- **SQL injection** — все запросы через SQLAlchemy ORM параметризованы.
- **Timing-атаки по ключам** — верификация через argon2 (постоянное время).
- **Утечка секретов в логах** — `SecretStr` в Settings, structlog-процессоры
  не включают секреты по ключам.
- **Race condition в статусах** — optimistic lock через ETag+If-Match.
- **Дубликаты при ретраях** — Idempotency-Key.

## Что требует внимания при деплое

- `.env` с реальными секретами **никогда** не коммитить (`.gitignore`, `gitleaks` в pre-commit).
- Запускать за reverse-proxy (nginx/traefik) с HTTPS-терминацией.
- Трастовые IP для `X-Forwarded-For` должны настраиваться на proxy-слое.
- ADMIN_BOOTSTRAP_KEY ротировать после создания первого администратора
  (или удалить из окружения).

## Reporting vulnerabilities

Нашли проблему — напишите в приватном порядке в issues с тегом `security`
или на `security@serviceflow.local`. Публичные issue для security-багов
открывать **не нужно**. Срок ответа — 72 часа.
