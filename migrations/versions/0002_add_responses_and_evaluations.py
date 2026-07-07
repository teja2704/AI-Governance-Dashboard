"""add responses and evaluations

Revision ID: 0002_add_responses_and_evaluations
Revises: 0001_initial_schema
Create Date: 2026-07-07 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_responses_and_evaluations"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_responses() -> None:
    op.create_table(
        "responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("response_length", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(
        "ix_responses_created_at",
        "responses",
        ["created_at"],
        unique=False
    )
    op.create_index(
        "ix_responses_id",
        "responses",
        ["id"],
        unique=False
    )
    op.create_index(
        "ix_responses_prompt_id",
        "responses",
        ["prompt_id"],
        unique=False
    )


def _create_evaluations() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_type", sa.String(length=20), nullable=False),
        sa.Column("evaluator_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("flags", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["evaluator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["response_id"], ["responses.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(
        "ix_evaluations_created_at",
        "evaluations",
        ["created_at"],
        unique=False
    )
    op.create_index(
        "ix_evaluations_evaluation_type",
        "evaluations",
        ["evaluation_type"],
        unique=False
    )
    op.create_index(
        "ix_evaluations_evaluator_id",
        "evaluations",
        ["evaluator_id"],
        unique=False
    )
    op.create_index(
        "ix_evaluations_id",
        "evaluations",
        ["id"],
        unique=False
    )
    op.create_index(
        "ix_evaluations_response_id",
        "evaluations",
        ["response_id"],
        unique=False
    )


def _backfill_existing_prompt_responses() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()

    prompts = sa.Table(
        "prompts",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("response", sa.Text()),
        sa.Column("model", sa.String(length=100)),
        sa.Column("status", sa.String(length=20)),
        sa.Column("response_length", sa.Integer()),
        sa.Column("timestamp", sa.DateTime(timezone=True))
    )
    responses = sa.Table(
        "responses",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("prompt_id", sa.Integer()),
        sa.Column("response", sa.Text()),
        sa.Column("model", sa.String(length=100)),
        sa.Column("status", sa.String(length=20)),
        sa.Column("response_length", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True))
    )

    prompt_rows = bind.execute(
        sa.select(
            prompts.c.id,
            prompts.c.response,
            prompts.c.model,
            prompts.c.status,
            prompts.c.response_length,
            prompts.c.timestamp
        ).where(prompts.c.response.is_not(None))
    ).all()

    for prompt in prompt_rows:
        existing_response = bind.execute(
            sa.select(responses.c.id)
            .where(responses.c.prompt_id == prompt.id)
            .limit(1)
        ).first()

        if existing_response:
            continue

        bind.execute(
            responses.insert().values(
                prompt_id=prompt.id,
                response=prompt.response,
                model=prompt.model,
                status=prompt.status,
                response_length=prompt.response_length,
                created_at=prompt.timestamp
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "responses" not in table_names:
        _create_responses()

    if "evaluations" not in table_names:
        _create_evaluations()

    _backfill_existing_prompt_responses()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "evaluations" in table_names:
        evaluation_indexes = {
            index["name"]
            for index in inspector.get_indexes("evaluations")
        }

        for index_name in [
            "ix_evaluations_created_at",
            "ix_evaluations_evaluation_type",
            "ix_evaluations_evaluator_id",
            "ix_evaluations_id",
            "ix_evaluations_response_id"
        ]:
            if index_name in evaluation_indexes:
                op.drop_index(index_name, table_name="evaluations")

        op.drop_table("evaluations")

    if "responses" in table_names:
        response_indexes = {
            index["name"]
            for index in inspector.get_indexes("responses")
        }

        for index_name in [
            "ix_responses_created_at",
            "ix_responses_id",
            "ix_responses_prompt_id"
        ]:
            if index_name in response_indexes:
                op.drop_index(index_name, table_name="responses")

        op.drop_table("responses")
