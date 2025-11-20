"""Add settings_json column to users table

Revision ID: add_settings_json_column
Revises: add_profile_column
Create Date: 2025-11-20 04:58:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_settings_json_column"
down_revision: Union[str, Sequence[str], None] = "add_profile_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add settings_json column to users table."""
	# Check if column exists first to avoid errors if it was partially applied
	conn = op.get_bind()
	inspector = sa.inspect(conn)
	columns = [c["name"] for c in inspector.get_columns("users")]

	if "settings_json" not in columns:
		op.add_column("users", sa.Column("settings_json", sa.JSON(), nullable=True, server_default="{}"))


def downgrade() -> None:
	"""Remove settings_json column from users table."""
	op.drop_column("users", "settings_json")
