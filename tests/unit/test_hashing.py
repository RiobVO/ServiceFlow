"""Юнит-тесты хеширования API-ключей."""

from __future__ import annotations

import pytest

from app.core.hashing import (
    PREFIX_LEN,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)

pytestmark = pytest.mark.unit


def test_generated_key_structure():
    issued = generate_api_key()
    assert len(issued.prefix) == PREFIX_LEN
    assert issued.last4 == issued.raw[-4:]
    assert issued.prefix == issued.raw[:PREFIX_LEN]
    assert issued.hash.startswith("$argon2")


def test_hash_verifies_only_exact_match():
    issued = generate_api_key()
    assert verify_api_key(issued.raw, issued.hash)
    assert not verify_api_key(issued.raw + "x", issued.hash)
    assert not verify_api_key("totally_other_key", issued.hash)


def test_two_generations_differ():
    a = generate_api_key()
    b = generate_api_key()
    assert a.raw != b.raw
    assert a.hash != b.hash


def test_hash_of_same_input_is_different_each_time():
    k = "some_plain_key"
    h1 = hash_api_key(k)
    h2 = hash_api_key(k)
    assert h1 != h2
    assert verify_api_key(k, h1)
    assert verify_api_key(k, h2)


def test_verify_tolerates_garbage_hash():
    assert not verify_api_key("anything", "not-even-a-hash")
