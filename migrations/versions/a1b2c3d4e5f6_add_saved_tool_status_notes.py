"""add saved_tool status and notes

Revision ID: a1b2c3d4e5f6
Revises: 6554af65b484
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '6554af65b484'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'saved_tools',
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='considering',
            nullable=False,
        ),
    )
    op.add_column(
        'saved_tools',
        sa.Column('notes', sa.String(length=2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('saved_tools', 'notes')
    op.drop_column('saved_tools', 'status')
