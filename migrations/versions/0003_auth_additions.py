"""Add auth additions

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25 18:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_auth_additions'
down_revision: Union[str, None] = '0002_responses_evals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email column, initially nullable to avoid errors on existing data
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Update existing users with a dummy email based on username
    op.execute("UPDATE users SET email = username || '@example.com' WHERE email IS NULL")
    
    # Alter column to be NOT NULL
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('email', existing_type=sa.String(length=255), nullable=False)

    # Create password_resets table
    op.create_table('password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('otp_code', sa.String(length=6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_id'), 'password_resets', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_password_resets_id'), table_name='password_resets')
    op.drop_table('password_resets')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
