"""Add Phase 3.3 fields for expanded job boards

Revision ID: 005_phase_3_3_fields
Revises: 004_add_calendar_tables
Create Date: 2025-11-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_phase_3_3_fields"
down_revision = "004_add_calendar_tables"
branch_labels = None
depends_on = None


def upgrade():
	"""Add new fields for Phase 3.3 job board integrations."""

	# Language and experience
	op.add_column("jobs", sa.Column("language_requirements", postgresql.ARRAY(sa.Text()), nullable=True))
	op.add_column("jobs", sa.Column("experience_level", sa.String(length=50), nullable=True))

	# Startup/equity fields
	op.add_column("jobs", sa.Column("equity_range", sa.String(length=100), nullable=True))
	op.add_column("jobs", sa.Column("funding_stage", sa.String(length=50), nullable=True))
	op.add_column("jobs", sa.Column("total_funding", sa.BigInteger(), nullable=True))
	op.add_column("jobs", sa.Column("investors", postgresql.ARRAY(sa.Text()), nullable=True))

	# Tech and culture
	# Check if tech_stack exists
	conn = op.get_bind()
	inspector = sa.inspect(conn)
	columns = [c['name'] for c in inspector.get_columns('jobs')]
	
	if 'tech_stack' not in columns:
		op.add_column("jobs", sa.Column("tech_stack", postgresql.ARRAY(sa.Text()), nullable=True))
		
	op.add_column("jobs", sa.Column("company_culture_tags", postgresql.ARRAY(sa.Text()), nullable=True))
	op.add_column("jobs", sa.Column("perks", postgresql.ARRAY(sa.Text()), nullable=True))

	# Swiss-specific
	op.add_column("jobs", sa.Column("work_permit_info", sa.Text(), nullable=True))
	op.add_column("jobs", sa.Column("workload_percentage", sa.Integer(), nullable=True))

	# Verification and media
	op.add_column("jobs", sa.Column("company_verified", sa.Boolean(), server_default="false", nullable=False))
	op.add_column("jobs", sa.Column("company_videos", postgresql.JSONB(), nullable=True))

	# Language tracking
	op.add_column("jobs", sa.Column("job_language", sa.String(length=5), server_default="en", nullable=False))

	# Add indexes for filtering
	op.create_index("idx_jobs_experience_level", "jobs", ["experience_level"])
	op.create_index("idx_jobs_funding_stage", "jobs", ["funding_stage"])
	op.create_index("idx_jobs_job_language", "jobs", ["job_language"])

	# Add GIN indexes for array fields (for fast array containment searches)
	op.create_index("idx_jobs_tech_stack", "jobs", ["tech_stack"], postgresql_using="gin")
	op.create_index("idx_jobs_culture_tags", "jobs", ["company_culture_tags"], postgresql_using="gin")
	op.create_index("idx_jobs_language_reqs", "jobs", ["language_requirements"], postgresql_using="gin")

	# Add check constraints
	op.create_check_constraint(
		"check_experience_level",
		"jobs",
		sa.column("experience_level").in_(
			["Internship", "Entry Level", "Junior", "Mid-Level", "Senior", "Lead", "Staff", "Principal", "Manager", "Director", "VP", "C-Level"]
		)
		| sa.column("experience_level").is_(None),
	)

	op.create_check_constraint(
		"check_funding_stage",
		"jobs",
		sa.column("funding_stage").in_(["Bootstrapped", "Pre-Seed", "Seed", "Series A", "Series B", "Series C", "Series D+", "Acquired", "Public"])
		| sa.column("funding_stage").is_(None),
	)

	op.create_check_constraint("check_job_language", "jobs", sa.column("job_language").in_(["en", "de", "fr", "it", "es"]))

	op.create_check_constraint(
		"check_workload_percentage",
		"jobs",
		sa.and_(sa.column("workload_percentage") >= 0, sa.column("workload_percentage") <= 100) | sa.column("workload_percentage").is_(None),
	)


def downgrade():
	"""Remove Phase 3.3 fields."""

	# Drop constraints
	op.drop_constraint("check_workload_percentage", "jobs", type_="check")
	op.drop_constraint("check_job_language", "jobs", type_="check")
	op.drop_constraint("check_funding_stage", "jobs", type_="check")
	op.drop_constraint("check_experience_level", "jobs", type_="check")

	# Drop indexes
	op.drop_index("idx_jobs_language_reqs", "jobs")
	op.drop_index("idx_jobs_culture_tags", "jobs")
	op.drop_index("idx_jobs_tech_stack", "jobs")
	op.drop_index("idx_jobs_job_language", "jobs")
	op.drop_index("idx_jobs_funding_stage", "jobs")
	op.drop_index("idx_jobs_experience_level", "jobs")

	# Drop columns
	op.drop_column("jobs", "job_language")
	op.drop_column("jobs", "company_videos")
	op.drop_column("jobs", "company_verified")
	op.drop_column("jobs", "workload_percentage")
	op.drop_column("jobs", "work_permit_info")
	op.drop_column("jobs", "perks")
	op.drop_column("jobs", "company_culture_tags")
	op.drop_column("jobs", "tech_stack")
	op.drop_column("jobs", "investors")
	op.drop_column("jobs", "total_funding")
	op.drop_column("jobs", "funding_stage")
	op.drop_column("jobs", "equity_range")
	op.drop_column("jobs", "experience_level")
	op.drop_column("jobs", "language_requirements")
