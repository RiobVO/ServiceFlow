"""Юнит-тесты утилит идемпотентности."""

from __future__ import annotations

import pytest

from app.core.idempotency import compute_body_hash, validate_key

pytestmark = pytest.mark.unit


def test_validate_key_accepts_normal_string():
    assert validate_key("abc-123") == "abc-123"


def test_validate_key_rejects_empty_and_overlong():
    assert validate_key("") is None
    assert validate_key(None) is None
    assert validate_key("x" * 129) is None


def test_body_hash_is_stable_regardless_of_key_order():
    a = compute_body_hash({"title": "t", "description": "d"})
    b = compute_body_hash({"description": "d", "title": "t"})
    assert a == b


def test_body_hash_differs_on_content_change():
    a = compute_body_hash({"title": "t"})
    b = compute_body_hash({"title": "t2"})
    assert a != b
