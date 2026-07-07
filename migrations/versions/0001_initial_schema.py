"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-07 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "prompts" not in table_names:
        op.create_table(
            "prompts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("response", sa.Text(), nullable=True),
            sa.Column("model", sa.String(length=100), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
            sa.Column("response_length", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index(
            "ix_prompts_id",
            "prompts",
            ["id"],
            unique=False
        )

    if "users" not in table_names:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=150), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index(
            "ix_users_id",
            "users",
            ["id"],
            unique=False
        )
        op.create_index(
            "ix_users_username",
            "users",
            ["username"],
            unique=True
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "users" in table_names:
        user_indexes = {
            index["name"]
            for index in inspector.get_indexes("users")
        }

        if "ix_users_username" in user_indexes:
            op.drop_index("ix_users_username", table_name="users")

        if "ix_users_id" in user_indexes:
            op.drop_index("ix_users_id", table_name="users")

        op.drop_table("users")

    if "prompts" in table_names:
        prompt_indexes = {
            index["name"]
            for index in inspector.get_indexes("prompts")
        }

        if "ix_prompts_id" in prompt_indexes:
            op.drop_index("ix_prompts_id", table_name="prompts")

        op.drop_table("prompts")
