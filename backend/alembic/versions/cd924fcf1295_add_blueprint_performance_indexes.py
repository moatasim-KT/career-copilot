"""add_blueprint_performance_indexes

Revision ID: cd924fcf1295
Revises: 79392a85c8a2
Create Date: 2025-10-21 15:39:29.041165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd924fcf1295'
down_revision: Union[str, Sequence[str], None] = '79392a85c8a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for Career Co-Pilot MVP blueprint features."""
    
    # Add performance indexes for blueprint features
    # These indexes optimize the recommendation engine, skill gap analysis, and analytics queries
    
    # Index for user_id on jobs table (for filtering jobs by user)
    try:
        op.create_index('ix_jobs_user_id', 'jobs', ['user_id'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Index for user_id on applications table (for filtering applications by user)
    try:
        op.create_index('ix_applications_user_id', 'applications', ['user_id'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Index for job_id on applications table (for joining applications with jobs)
    try:
        op.create_index('ix_applications_job_id', 'applications', ['job_id'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Composite index for job status filtering (user_id + status)
    # Optimizes queries like: "get all not_applied jobs for user"
    try:
        op.create_index('ix_jobs_user_status', 'jobs', ['user_id', 'status'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Composite index for application tracking (user_id + status)
    # Optimizes queries like: "get all interview applications for user"
    try:
        op.create_index('ix_applications_user_status', 'applications', ['user_id', 'status'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Composite index for job recommendations (user_id + created_at)
    # Optimizes queries that sort jobs by date for a user
    try:
        op.create_index('ix_jobs_user_created', 'jobs', ['user_id', 'created_at'], unique=False)
    except Exception:
        pass  # Index may already exist


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop indexes in reverse order
    try:
        op.drop_index('ix_jobs_user_created', table_name='jobs')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_applications_user_status', table_name='applications')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_jobs_user_status', table_name='jobs')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_applications_job_id', table_name='applications')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_applications_user_id', table_name='applications')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_jobs_user_id', table_name='jobs')
    except Exception:
        pass
