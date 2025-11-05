"""add_prefer_remote_jobs_to_user

Revision ID: 6b17ab364809
Revises: ae995c518187
Create Date: 2025-11-05 01:37:56.684023

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b17ab364809"
down_revision: Union[str, Sequence[str], None] = "ae995c518187"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Upgrade schema."""
	# Add prefer_remote_jobs column to users table
	op.add_column("users", sa.Column("prefer_remote_jobs", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
	"""Downgrade schema."""
	# Remove prefer_remote_jobs column from users table
	op.drop_column("users", "prefer_remote_jobs")
