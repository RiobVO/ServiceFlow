"""Доменные исключения ServiceFlow.

Правило: сервисы и policies кидают только доменные исключения.
HTTP-семантика (коды, Problem Details) — исключительно в app/core/errors.py.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Базовое доменное исключение. HTTP-статус определяется в маппере."""

    # Машиночитаемый стабильный код ошибки (попадает в Problem Details.code).
    code: str = "domain_error"
    # HTTP-статус по умолчанию для данного типа ошибки.
    http_status: int = 400
    # Человекочитаемое сообщение по умолчанию.
    default_message: str = "Доменная ошибка."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        self.message = message or self.default_message
        if code is not None:
            self.code = code
        self.details = details
        super().__init__(self.message)


# ---------- 400 BAD REQUEST ----------

class ValidationFailed(DomainError):
    code = "validation_failed"
    http_status = 400
    default_message = "Некорректные данные."


class BusinessRuleViolation(DomainError):
    """Нарушение бизнес-правила (например, попытка изменить terminal-статус)."""

    code = "business_rule_violation"
    http_status = 400
    default_message = "Нарушение бизнес-правила."


class InvalidStatusTransition(BusinessRuleViolation):
    code = "invalid_status_transition"
    default_message = "Невалидный переход статуса."


class StatusIsTerminal(BusinessRuleViolation):
    code = "status_is_terminal"
    default_message = "Статус заявки окончательный."


class StatusAlreadySet(BusinessRuleViolation):
    code = "status_is_already_set"
    default_message = "Заявка уже имеет этот статус."


class InProgressRequiresAssignee(BusinessRuleViolation):
    code = "in_progress_requires_assignee"
    default_message = "Для статуса IN_PROGRESS нужен исполнитель."


# ---------- 401 UNAUTHORIZED ----------

class AuthenticationError(DomainError):
    code = "authentication_error"
    http_status = 401
    default_message = "Ошибка аутентификации."


class MissingApiKey(AuthenticationError):
    code = "missing_api_key"
    default_message = "Требуется API-ключ в заголовке X-API-Key."


class InvalidApiKey(AuthenticationError):
    code = "invalid_api_key"
    default_message = "Неверный или неактивный API-ключ."


# ---------- 403 FORBIDDEN ----------

class PermissionDenied(DomainError):
    code = "permission_denied"
    http_status = 403
    default_message = "Нет прав на это действие."


class UserInactive(PermissionDenied):
    code = "user_inactive"
    default_message = "Учётная запись деактивирована."


class AdminOnly(PermissionDenied):
    code = "admin_only"
    default_message = "Эндпоинт доступен только администраторам."


class AgentOrAdminOnly(PermissionDenied):
    code = "agent_or_admin_only"
    default_message = "Эндпоинт доступен только AGENT или ADMIN."


# ---------- 404 NOT FOUND ----------

class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404
    default_message = "Объект не найден."


class UserNotFound(NotFoundError):
    code = "user_not_found"
    default_message = "Пользователь не найден."


class RequestNotFound(NotFoundError):
    code = "request_not_found"
    default_message = "Заявка не найдена."


class AssigneeNotFound(NotFoundError):
    code = "assignee_not_found"
    default_message = "Указанный исполнитель не найден."


# ---------- 409 CONFLICT ----------

class ConflictError(DomainError):
    code = "conflict"
    http_status = 409
    default_message = "Конфликт состояния ресурса."


class EmailAlreadyExists(ConflictError):
    code = "email_already_exists"
    default_message = "Пользователь с таким email уже существует."


class OptimisticLockFailed(ConflictError):
    code = "optimistic_lock_failed"
    default_message = "Ресурс был изменён другим запросом (ETag не совпал)."
    http_status = 412


class IdempotencyKeyConflict(ConflictError):
    code = "idempotency_key_conflict"
    default_message = "Idempotency-Key уже использован с другим телом запроса."
