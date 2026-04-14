"""Хеширование и верификация API-ключей (argon2id).

API-ключи **никогда** не хранятся в БД в открытом виде. Для аутентификации:
    1) по префиксу (первые 8 символов) находим кандидатов → O(log N);
    2) сравниваем полный ключ с хешем argon2.verify в постоянном времени
       относительно длины (устойчивость к timing-атакам).

Структура хранения:
    api_key_prefix:  первые PREFIX_LEN символов сырого ключа (индекс)
    api_key_last4:   последние 4 символа (для UI: "...abcd")
    api_key_hash:    argon2id-хеш полного сырого ключа

Параметры argon2 берутся у argon2-cffi (PasswordHasher) — безопасные дефолты,
подобранные сопровождающими библиотеки; при необходимости тюним через ENV.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

PREFIX_LEN = 8
LAST_LEN = 4
RAW_KEY_BYTES = 32  # 256 бит энтропии

# Один глобальный hasher — внутренне потокобезопасен.
_hasher = PasswordHasher()


@dataclass(frozen=True, slots=True)
class IssuedKey:
    """Результат выпуска нового API-ключа."""

    raw: str          # показать клиенту один раз
    prefix: str       # хранить в БД
    last4: str        # хранить в БД
    hash: str         # хранить в БД


def generate_api_key() -> IssuedKey:
    """Генерирует новый API-ключ и его производные для хранения."""
    raw = secrets.token_urlsafe(RAW_KEY_BYTES)
    return IssuedKey(
        raw=raw,
        prefix=raw[:PREFIX_LEN],
        last4=raw[-LAST_LEN:],
        hash=_hasher.hash(raw),
    )


def hash_api_key(raw: str) -> str:
    """Хеширует уже существующий сырой ключ (для data-миграции)."""
    return _hasher.hash(raw)


def extract_prefix(raw: str) -> str:
    return raw[:PREFIX_LEN]


def extract_last4(raw: str) -> str:
    return raw[-LAST_LEN:]


def verify_api_key(raw: str, stored_hash: str) -> bool:
    """Проверяет сырой ключ против argon2-хеша.

    Возвращает True при совпадении. Исключения argon2 поглощаются —
    любой сбой верификации интерпретируется как «не совпал».
    """
    try:
        return _hasher.verify(stored_hash, raw)
    except VerifyMismatchError:
        return False
    except Exception:
        # Порченый хеш или неверный формат — также считаем несовпадением.
        return False


def needs_rehash(stored_hash: str) -> bool:
    """Если параметры argon2 устарели (апгрейд библиотеки) — хеш стоит перевыпустить."""
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except Exception:
        return False
