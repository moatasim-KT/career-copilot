"""Add profile column to users table

Revision ID: add_profile_column
Revises: add_document_content_field
Create Date: 2025-11-20 04:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_profile_column"
down_revision: Union[str, Sequence[str], None] = "add_document_content_field"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add profile column to users table."""
	# Check if column exists first to avoid errors if it was partially applied
	conn = op.get_bind()
	inspector = sa.inspect(conn)
	columns = [c["name"] for c in inspector.get_columns("users")]

	if "profile" not in columns:
		op.add_column("users", sa.Column("profile", sa.JSON(), nullable=True, server_default="{}"))


def downgrade() -> None:
	"""Remove profile column from users table."""
	op.drop_column("users", "profile")
