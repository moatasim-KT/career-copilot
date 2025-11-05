"""add_job_deduplication_index

Revision ID: ae995c518187
Revises: 3e72c1c42810
Create Date: 2025-11-04 13:17:06.490104

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae995c518187"
down_revision: Union[str, Sequence[str], None] = "3e72c1c42810"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add composite index and fingerprint column for job deduplication."""

	# Add job_fingerprint column for faster duplicate detection
	op.add_column("jobs", sa.Column("job_fingerprint", sa.String(32), nullable=True, index=True))

	# Create composite index for efficient duplicate checking
	# Index on (user_id, company, title, location) for exact match queries
	op.create_index("ix_jobs_user_company_title_location", "jobs", ["user_id", "company", "title", "location"], unique=False)

	# Create index on application_url for URL-based deduplication
	op.create_index("ix_jobs_application_url", "jobs", ["application_url"], unique=False)

	# Note: We don't create a unique constraint because:
	# 1. Same job might be legitimately re-posted after some time
	# 2. Different users might save the same job
	# 3. We handle deduplication at the application level with more sophisticated logic


def downgrade() -> None:
	"""Remove deduplication indexes and fingerprint column."""

	# Drop indexes
	op.drop_index("ix_jobs_application_url", table_name="jobs")
	op.drop_index("ix_jobs_user_company_title_location", table_name="jobs")

	# Drop fingerprint column
	op.drop_column("jobs", "job_fingerprint")
