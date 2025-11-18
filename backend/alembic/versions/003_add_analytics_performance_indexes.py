"""Add analytics performance indexes

Revision ID: 003_analytics_indexes
Revises: 002_add_notification_tables
Create Date: 2024-11-12 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003_analytics_indexes"
down_revision = "002_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
	"""Add indexes to optimize analytics queries"""

	# Applications table indexes for analytics
	# Index for date-based queries (trends, time series)
	op.create_index("idx_applications_user_applied_date", "applications", ["user_id", "applied_date"], unique=False)

	# Index for status-based analytics
	op.create_index("idx_applications_user_status", "applications", ["user_id", "status"], unique=False)

	# Composite index for date range and status queries
	op.create_index("idx_applications_user_date_status", "applications", ["user_id", "applied_date", "status"], unique=False)

	# Jobs table indexes for analytics
	# Index for company-based analytics
	op.create_index("idx_jobs_user_company", "jobs", ["user_id", "company"], unique=False)

	# Index for tech stack queries (if using JSON queries)
	# Note: This creates a GIN index for PostgreSQL JSON queries

	op.execute("CREATE INDEX idx_jobs_tech_stack_gin ON jobs USING GIN (tech_stack)")

	# Index for date-based job queries
	op.create_index("idx_jobs_user_created_at", "jobs", ["user_id", "created_at"], unique=False)

	# Users table index for skills
	op.execute("CREATE INDEX idx_users_skills_gin ON users USING GIN (skills)")


def downgrade() -> None:
	"""Remove analytics performance indexes"""

	# Drop applications indexes
	op.drop_index("idx_applications_user_applied_date", table_name="applications")
	op.drop_index("idx_applications_user_status", table_name="applications")
	op.drop_index("idx_applications_user_date_status", table_name="applications")

	# Drop jobs indexes
	op.drop_index("idx_jobs_user_company", table_name="jobs")
	op.drop_index("idx_jobs_user_created_at", table_name="jobs")

	# Drop JSON indexes
	op.execute("DROP INDEX IF EXISTS idx_jobs_tech_stack_gin")
	op.execute("DROP INDEX IF EXISTS idx_users_skills_gin")
