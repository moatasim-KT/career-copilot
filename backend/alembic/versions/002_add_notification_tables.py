"""add notification tables

Revision ID: 002_notifications
Revises: 001_search_perf
Create Date: 2025-01-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_notifications'
down_revision: Union[str, None] = '001_search_perf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notification and notification_preferences tables"""
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum(
            'JOB_STATUS_CHANGE',
            'APPLICATION_UPDATE',
            'INTERVIEW_REMINDER',
            'NEW_JOB_MATCH',
            'APPLICATION_DEADLINE',
            'SKILL_GAP_REPORT',
            'SYSTEM_ANNOUNCEMENT',
            'MORNING_BRIEFING',
            'EVENING_UPDATE',
            name='notificationtype'
        ), nullable=False),
        sa.Column('priority', sa.Enum(
            'LOW',
            'MEDIUM',
            'HIGH',
            'URGENT',
            name='notificationpriority'
        ), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for notifications table
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    
    # Create composite index for common queries (user_id + is_read + created_at)
    op.create_index(
        'ix_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read', 'created_at']
    )
    
    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # Channel preferences
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # Event type preferences
        sa.Column('job_status_change_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('application_update_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('interview_reminder_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('new_job_match_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('application_deadline_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('skill_gap_report_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('system_announcement_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('morning_briefing_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('evening_update_enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # Timing preferences
        sa.Column('morning_briefing_time', sa.String(length=5), nullable=False, server_default='08:00'),
        sa.Column('evening_update_time', sa.String(length=5), nullable=False, server_default='18:00'),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        
        # Frequency preferences
        sa.Column('digest_frequency', sa.String(length=20), nullable=False, server_default='daily'),
        
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create indexes for notification_preferences table
    op.create_index('ix_notification_preferences_id', 'notification_preferences', ['id'])
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    """Drop notification and notification_preferences tables"""
    
    # Drop indexes first
    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
    op.drop_index('ix_notification_preferences_id', table_name='notification_preferences')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_id', table_name='notifications')
    
    # Drop tables
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS notificationpriority')
    op.execute('DROP TYPE IF EXISTS notificationtype')
