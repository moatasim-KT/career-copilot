"""Add content field to documents table for database storage

Revision ID: add_document_content_field
Revises: career_resources_001
Create Date: 2025-01-11 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_document_content_field"
down_revision: Union[str, Sequence[str], None] = "005_phase_3_3_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add content field to documents table for storing file content in database."""
	# Add content column to documents table
	op.add_column("documents", sa.Column("content", sa.LargeBinary(), nullable=False))


def downgrade() -> None:
	"""Remove content field from documents table."""
	op.drop_column("documents", "content")
