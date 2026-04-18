"""hash api keys (argon2)

Revision ID: b1a2c3d4e5f6
Revises: e665755dea52
Create Date: 2026-04-18 00:00:00.000000

Миграция переводит хранение API-ключей на argon2id:
    - добавляем api_key_prefix, api_key_last4, api_key_hash
    - хешируем существующие plaintext-значения api_key
    - удаляем колонку api_key

Downgrade не поддерживается: из argon2-хеша нельзя восстановить сырой ключ.
Для отката потребуется вручную перевыпустить ключи всем пользователям.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.hashing import extract_last4, extract_prefix, hash_api_key

revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e665755dea52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Добавляем новые колонки как nullable
    op.add_column("users", sa.Column("api_key_prefix", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("api_key_last4", sa.String(length=8), nullable=True))
    op.add_column("users", sa.Column("api_key_hash", sa.String(length=255), nullable=True))

    # 2) Data migration: хешируем существующие ключи
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, api_key FROM users WHERE api_key IS NOT NULL")).fetchall()
    for row in rows:
        user_id, raw_key = row[0], row[1]
        if not raw_key:
            continue
        bind.execute(
            sa.text(
                "UPDATE users SET api_key_prefix = :p, api_key_last4 = :l, api_key_hash = :h WHERE id = :id"
            ),
            {
                "p": extract_prefix(raw_key),
                "l": extract_last4(raw_key),
                "h": hash_api_key(raw_key),
                "id": user_id,
            },
        )

    # 3) Ставим NOT NULL и индекс на префикс
    op.alter_column("users", "api_key_prefix", nullable=False)
    op.alter_column("users", "api_key_last4", nullable=False)
    op.alter_column("users", "api_key_hash", nullable=False)
    op.create_index("ix_users_api_key_prefix", "users", ["api_key_prefix"])

    # 4) Удаляем старую колонку api_key (если она вообще есть).
    #    Имя уникального индекса/констрейнта может отличаться в разных
    #    инсталляциях — опрашиваем inspector'ом и дропаем только то, что есть.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    users_columns = {c["name"] for c in inspector.get_columns("users")}

    if "api_key" in users_columns:
        for ix in inspector.get_indexes("users"):
            if "api_key" in ix.get("column_names", []):
                op.drop_index(ix["name"], table_name="users")

        for uc in inspector.get_unique_constraints("users"):
            if "api_key" in uc.get("column_names", []):
                op.drop_constraint(uc["name"], "users", type_="unique")

        op.drop_column("users", "api_key")


def downgrade() -> None:
    # Восстановление plaintext из argon2 невозможно.
    # Добавляем пустую колонку api_key как nullable — админ должен ротировать ключи.
    op.add_column("users", sa.Column("api_key", sa.String(), nullable=True))
    op.create_index("ix_users_api_key", "users", ["api_key"], unique=True)

    op.drop_index("ix_users_api_key_prefix", table_name="users")
    op.drop_column("users", "api_key_hash")
    op.drop_column("users", "api_key_last4")
    op.drop_column("users", "api_key_prefix")
