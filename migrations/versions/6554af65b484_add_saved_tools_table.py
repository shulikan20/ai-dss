"""add saved_tools table

Revision ID: 6554af65b484
Revises: d701e868153b
Create Date: 2026-06-09 23:15:10.272516

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '6554af65b484'
down_revision: Union[str, Sequence[str], None] = 'd701e868153b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability_id', sa.String(length=100), nullable=False),
        sa.Column('capability_name', sa.String(length=255), nullable=True),
        sa.Column('saved_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_saved_tools_user_capability',
        'saved_tools',
        ['user_id', 'capability_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_saved_tools_user_capability', table_name='saved_tools')
    op.drop_table('saved_tools')