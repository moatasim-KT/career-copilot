"""Add career resources tables

Revision ID: career_resources_001
Revises: 6b17ab364809
Create Date: 2025-11-06 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "career_resources_001"
down_revision: Union[str, Sequence[str], None] = "6b17ab364809"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Create career resources tables."""
	# Career Resources table
	op.create_table(
		"career_resources",
		sa.Column("id", sa.String(), nullable=False),
		sa.Column("title", sa.String(length=255), nullable=False),
		sa.Column("description", sa.Text(), nullable=False),
		sa.Column("type", sa.String(length=50), nullable=False),
		sa.Column("provider", sa.String(length=100), nullable=False),
		sa.Column("url", sa.Text(), nullable=False),
		sa.Column("skills", postgresql.ARRAY(sa.String()), nullable=False),
		sa.Column("difficulty", sa.String(length=50), nullable=False),
		sa.Column("duration", sa.String(length=100), nullable=True),
		sa.Column("price", sa.String(length=50), nullable=False),
		sa.Column("rating", sa.Float(), nullable=True),
		sa.Column("base_relevance_score", sa.Integer(), nullable=True),
		sa.Column("image_url", sa.Text(), nullable=True),
		sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
		sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("prerequisites", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("learning_outcomes", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.Column("updated_at", sa.DateTime(), nullable=True),
		sa.Column("deleted_at", sa.DateTime(), nullable=True),
		sa.PrimaryKeyConstraint("id"),
	)
	op.create_index("idx_resource_type_difficulty", "career_resources", ["type", "difficulty"])
	op.create_index("idx_resource_active", "career_resources", ["is_active"])
	op.create_index("idx_resource_rating", "career_resources", ["rating"])
	op.create_index(op.f("ix_career_resources_title"), "career_resources", ["title"])
	op.create_index(op.f("ix_career_resources_type"), "career_resources", ["type"])

	# Resource Bookmarks table
	op.create_table(
		"resource_bookmarks",
		sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("user_id", sa.Integer(), nullable=False),
		sa.Column("resource_id", sa.String(), nullable=False),
		sa.Column("notes", sa.Text(), nullable=True),
		sa.Column("priority", sa.String(length=20), nullable=True, server_default="medium"),
		sa.Column("status", sa.String(length=50), nullable=True, server_default="to_learn"),
		sa.Column("progress_percentage", sa.Integer(), nullable=True, server_default="0"),
		sa.Column("estimated_completion_date", sa.DateTime(), nullable=True),
		sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.Column("updated_at", sa.DateTime(), nullable=True),
		sa.Column("completed_at", sa.DateTime(), nullable=True),
		sa.Column("archived_at", sa.DateTime(), nullable=True),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["resource_id"], ["career_resources.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("user_id", "resource_id", name="uq_user_resource_bookmark"),
	)
	op.create_index("idx_bookmark_user_status", "resource_bookmarks", ["user_id", "status"])
	op.create_index("idx_bookmark_created", "resource_bookmarks", ["created_at"])

	# Resource Feedback table
	op.create_table(
		"resource_feedback",
		sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("user_id", sa.Integer(), nullable=False),
		sa.Column("resource_id", sa.String(), nullable=False),
		sa.Column("is_helpful", sa.Boolean(), nullable=False),
		sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
		sa.Column("rating", sa.Float(), nullable=True),
		sa.Column("time_spent_hours", sa.Float(), nullable=True),
		sa.Column("notes", sa.Text(), nullable=True),
		sa.Column("content_quality", sa.Integer(), nullable=True),
		sa.Column("instruction_clarity", sa.Integer(), nullable=True),
		sa.Column("practical_value", sa.Integer(), nullable=True),
		sa.Column("difficulty_match", sa.Integer(), nullable=True),
		sa.Column("would_recommend", sa.Boolean(), nullable=True),
		sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.Column("updated_at", sa.DateTime(), nullable=True),
		sa.Column("completed_at", sa.DateTime(), nullable=True),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["resource_id"], ["career_resources.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("user_id", "resource_id", name="uq_user_resource_feedback"),
	)
	op.create_index("idx_feedback_user", "resource_feedback", ["user_id"])
	op.create_index("idx_feedback_resource", "resource_feedback", ["resource_id"])
	op.create_index("idx_feedback_helpful", "resource_feedback", ["is_helpful"])
	op.create_index("idx_feedback_completed", "resource_feedback", ["completed"])

	# Resource Views table
	op.create_table(
		"resource_views",
		sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("user_id", sa.Integer(), nullable=False),
		sa.Column("resource_id", sa.String(), nullable=False),
		sa.Column("view_duration_seconds", sa.Integer(), nullable=True),
		sa.Column("clicked_through", sa.Boolean(), nullable=True, server_default="false"),
		sa.Column("source", sa.String(length=100), nullable=True),
		sa.Column("filters_used", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("viewed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["resource_id"], ["career_resources.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
	)
	op.create_index("idx_view_user_resource", "resource_views", ["user_id", "resource_id"])
	op.create_index("idx_view_timestamp", "resource_views", ["viewed_at"])
	op.create_index("idx_view_clicked", "resource_views", ["clicked_through"])

	# Learning Paths table
	op.create_table(
		"learning_paths",
		sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("name", sa.String(length=255), nullable=False),
		sa.Column("description", sa.Text(), nullable=False),
		sa.Column("target_role", sa.String(length=100), nullable=True),
		sa.Column("difficulty", sa.String(length=50), nullable=False),
		sa.Column("estimated_duration_weeks", sa.Integer(), nullable=True),
		sa.Column("resource_ids", postgresql.ARRAY(sa.String()), nullable=False),
		sa.Column("milestones", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
		sa.Column("created_by_user_id", sa.Integer(), nullable=True),
		sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.Column("updated_at", sa.DateTime(), nullable=True),
		sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
		sa.PrimaryKeyConstraint("id"),
	)
	op.create_index("idx_learning_path_active", "learning_paths", ["is_active"])
	op.create_index("idx_learning_path_role", "learning_paths", ["target_role"])

	# Learning Path Enrollments table
	op.create_table(
		"learning_path_enrollments",
		sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("user_id", sa.Integer(), nullable=False),
		sa.Column("learning_path_id", postgresql.UUID(as_uuid=True), nullable=False),
		sa.Column("current_resource_index", sa.Integer(), nullable=True, server_default="0"),
		sa.Column("completed_resource_ids", postgresql.ARRAY(sa.String()), nullable=True),
		sa.Column("progress_percentage", sa.Integer(), nullable=True, server_default="0"),
		sa.Column("status", sa.String(length=50), nullable=True, server_default="active"),
		sa.Column("enrolled_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
		sa.Column("last_activity_at", sa.DateTime(), nullable=True),
		sa.Column("completed_at", sa.DateTime(), nullable=True),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("user_id", "learning_path_id", name="uq_user_learning_path"),
	)
	op.create_index("idx_enrollment_user_status", "learning_path_enrollments", ["user_id", "status"])


def downgrade() -> None:
	"""Drop career resources tables."""
	op.drop_index("idx_enrollment_user_status", table_name="learning_path_enrollments")
	op.drop_table("learning_path_enrollments")

	op.drop_index("idx_learning_path_role", table_name="learning_paths")
	op.drop_index("idx_learning_path_active", table_name="learning_paths")
	op.drop_table("learning_paths")

	op.drop_index("idx_view_clicked", table_name="resource_views")
	op.drop_index("idx_view_timestamp", table_name="resource_views")
	op.drop_index("idx_view_user_resource", table_name="resource_views")
	op.drop_table("resource_views")

	op.drop_index("idx_feedback_completed", table_name="resource_feedback")
	op.drop_index("idx_feedback_helpful", table_name="resource_feedback")
	op.drop_index("idx_feedback_resource", table_name="resource_feedback")
	op.drop_index("idx_feedback_user", table_name="resource_feedback")
	op.drop_table("resource_feedback")

	op.drop_index("idx_bookmark_created", table_name="resource_bookmarks")
	op.drop_index("idx_bookmark_user_status", table_name="resource_bookmarks")
	op.drop_table("resource_bookmarks")

	op.drop_index(op.f("ix_career_resources_type"), table_name="career_resources")
	op.drop_index(op.f("ix_career_resources_title"), table_name="career_resources")
	op.drop_index("idx_resource_rating", table_name="career_resources")
	op.drop_index("idx_resource_active", table_name="career_resources")
	op.drop_index("idx_resource_type_difficulty", table_name="career_resources")
	op.drop_table("career_resources")
