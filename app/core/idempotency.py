"""Утилиты идемпотентности.

Ключ идемпотентности — заголовок Idempotency-Key. Мы привязываем его
к (user_id, method, path), чтобы один и тот же ключ можно было
использовать в разных эндпоинтах/пользователями без коллизий.

Повторный запрос с тем же ключом и телом → сохранённый ответ.
Тем же ключом с другим телом → 409 idempotency_key_conflict.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

_MAX_KEY_LEN = 128


def validate_key(key: str | None) -> str | None:
    """Возвращает валидный ключ или None (фича опциональна)."""
    if key is None:
        return None
    key = key.strip()
    if not key or len(key) > _MAX_KEY_LEN or not key.isprintable():
        return None
    return key


def compute_body_hash(payload: Any) -> str:
    """Детерминированный хеш тела запроса.

    json.dumps с sort_keys + separators=(",",":") даёт каноническую форму,
    независимую от порядка ключей и пробелов.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
