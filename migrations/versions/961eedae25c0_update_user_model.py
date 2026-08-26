"""update_user_model

Revision ID: 961eedae25c0
Revises: 0003_auth_additions
Create Date: 2026-08-25 19:58:02.726869
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '961eedae25c0'
down_revision: str | None = '0003_auth_additions'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_column_names(inspector, table: str) -> set:
    return {col['name'] for col in inspector.get_columns(table)}


def _get_index_names(inspector, table: str) -> set:
    return {idx['name'] for idx in inspector.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = _get_column_names(inspector, 'users')
    existing_idxs = _get_index_names(inspector, 'users')

    # ── Step 1: add first_name / last_name as NULLABLE ───────────────────────
    # This succeeds even when existing rows are present because no NOT NULL
    # constraint is enforced yet — existing rows get NULL, which is valid.
    if 'first_name' not in existing_cols:
        op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
    if 'last_name' not in existing_cols:
        op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))

    # ── Step 2: backfill existing rows ────────────────────────────────────────
    # Use Python-level logic so this is dialect-agnostic (SPLIT_PART is
    # Postgres-only and would break SQLite used in local/CI testing).
    # first_name  = portion of email before '@'  e.g. "Teja" from "Teja@example.com"
    # last_name   = '' (empty string) — no source data exists to derive a real name
    # Both are user-editable after login so a placeholder is acceptable.
    users_t = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('email', sa.String),
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
    )
    rows = bind.execute(
        sa.select(users_t.c.id, users_t.c.email).where(
            (users_t.c.first_name == None) | (users_t.c.first_name == '')  # noqa: E711
        )
    ).fetchall()
    for row_id, email in rows:
        derived = email.split('@')[0] if email else 'Unknown'
        bind.execute(
            sa.update(users_t)
            .where(users_t.c.id == row_id)
            .values(first_name=derived, last_name='')
        )

    # ── Step 3: enforce NOT NULL now that every row has a value ──────────────
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('first_name',
                               existing_type=sa.String(length=100),
                               nullable=False)
        batch_op.alter_column('last_name',
                               existing_type=sa.String(length=100),
                               nullable=False)

    # ── Other columns (nullable — no backfill needed) ─────────────────────────
    if 'google_id' not in existing_cols:
        op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))
    if 'avatar_url' not in existing_cols:
        op.add_column('users', sa.Column('avatar_url', sa.String(length=255), nullable=True))

    # ── Drop username index and column ────────────────────────────────────────
    if 'ix_users_username' in existing_idxs:
        op.drop_index(op.f('ix_users_username'), table_name='users')

    if 'ix_users_google_id' not in existing_idxs:
        op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)

    if 'username' in existing_cols:
        op.drop_column('users', 'username')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = _get_column_names(inspector, 'users')
    existing_idxs = _get_index_names(inspector, 'users')

    if 'username' not in existing_cols:
        op.add_column('users', sa.Column('username', sa.VARCHAR(length=150), nullable=False))

    if 'ix_users_google_id' in existing_idxs:
        op.drop_index(op.f('ix_users_google_id'), table_name='users')

    if 'ix_users_username' not in existing_idxs:
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    if 'avatar_url' in existing_cols:
        op.drop_column('users', 'avatar_url')
    if 'google_id' in existing_cols:
        op.drop_column('users', 'google_id')
    if 'last_name' in existing_cols:
        op.drop_column('users', 'last_name')
    if 'first_name' in existing_cols:
        op.drop_column('users', 'first_name')

