"""add_search_performance_indexes

Revision ID: 001_search_perf
Revises: 32b030e445af
Create Date: 2025-11-11 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_search_perf"
down_revision: Union[str, Sequence[str], None] = "32b030e445af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add indexes for search performance optimization."""

	# Job search indexes
	# Note: Some indexes already exist (company, title, status, created_at, user_id)
	# We'll add composite indexes for common search patterns
	
	# Composite index for location-based searches
	op.create_index(
		"ix_jobs_user_location",
		"jobs",
		["user_id", "location"],
		unique=False
	)
	
	# Composite index for remote job searches
	op.create_index(
		"ix_jobs_user_remote",
		"jobs",
		["user_id", "remote_option"],
		unique=False
	)
	
	# Composite index for job type searches
	op.create_index(
		"ix_jobs_user_type",
		"jobs",
		["user_id", "job_type"],
		unique=False
	)
	
	# Composite index for salary range searches
	op.create_index(
		"ix_jobs_user_salary",
		"jobs",
		["user_id", "salary_min", "salary_max"],
		unique=False
	)
	
	# Application search indexes
	# Composite index for status-based searches (already has status index, add composite)
	op.create_index(
		"ix_applications_user_status",
		"applications",
		["user_id", "status"],
		unique=False
	)
	
	# Composite index for date range searches
	op.create_index(
		"ix_applications_user_created",
		"applications",
		["user_id", "created_at"],
		unique=False
	)
	
	# Composite index for applied date searches
	op.create_index(
		"ix_applications_user_applied",
		"applications",
		["user_id", "applied_date"],
		unique=False
	)
	
	# Composite index for job-application joins
	op.create_index(
		"ix_applications_job_user",
		"applications",
		["job_id", "user_id"],
		unique=False
	)


def downgrade() -> None:
	"""Remove search performance indexes."""

	# Drop job indexes
	op.drop_index("ix_jobs_user_location", table_name="jobs")
	op.drop_index("ix_jobs_user_remote", table_name="jobs")
	op.drop_index("ix_jobs_user_type", table_name="jobs")
	op.drop_index("ix_jobs_user_salary", table_name="jobs")
	
	# Drop application indexes
	op.drop_index("ix_applications_user_status", table_name="applications")
	op.drop_index("ix_applications_user_created", table_name="applications")
	op.drop_index("ix_applications_user_applied", table_name="applications")
	op.drop_index("ix_applications_job_user", table_name="applications")
