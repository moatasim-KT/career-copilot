"""Merge migration branches

Revision ID: c22e4329ae15
Revises: 002_add_analysis_history_and_agent_executions, add_vector_store_tables
Create Date: 2025-10-06 01:23:35.063379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c22e4329ae15'
down_revision: Union[str, None] = ('002_add_analysis_history_and_agent_executions', 'add_vector_store_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass