# Contributing

## Локальный dev

```bash
docker compose --profile dev up -d db redis pgadmin
cp .env.example .env  # ADMIN_BOOTSTRAP_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

## Перед коммитом

```bash
pre-commit install
pre-commit run --all-files
pytest -m unit
```

## Архитектурные правила

- Сервисы не импортируют FastAPI и не возвращают HTTP-коды.
  Только `DomainError`-потомки; HTTP-семантика — в `app/core/errors.py`.
- Репозиторий без `commit`/`rollback` — транзакцию держит UoW.
- FSM заявок живёт в `app/domain/`, без I/O; покрывается юнит-тестами.
- Каждая новая ошибка — подкласс `DomainError` с полями `code`, `http_status`.
- Любые новые события пишутся в `outbox_events` в той же транзакции.

## Commits

Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`, `build:`.
Тело — что и **почему**, не как.

## Pull Request

- Маленький диф, ≤ 400 строк. Крупный рефакторинг — отдельным PR.
- Новый публичный эндпоинт → запись в `docs/api.md`, обновление OpenAPI (сам сгенерится).
- Изменение контракта ошибок → запись в `CHANGELOG.md` в разделе **Changed** с миграционным словом.
- Покрытие тестами — не снижаем ниже 85%.

## ADR

Любое значимое архитектурное решение (выбор библиотеки, паттерна, разметка данных)
фиксируется в `docs/adr/NNNN-title.md` по шаблону `docs/adr/template.md`.
