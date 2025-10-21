"""Add user settings table

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add user settings table."""
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ai_model_preference', sa.String(100), nullable=False, server_default='gpt-3.5-turbo'),
        sa.Column('analysis_depth', sa.String(50), nullable=False, server_default='normal'),
        sa.Column('email_notifications_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('slack_notifications_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('docusign_notifications_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('risk_threshold_low', sa.DECIMAL(3, 2), nullable=False, server_default='0.30'),
        sa.Column('risk_threshold_medium', sa.DECIMAL(3, 2), nullable=False, server_default='0.60'),
        sa.Column('risk_threshold_high', sa.DECIMAL(3, 2), nullable=False, server_default='0.80'),
        sa.Column('auto_generate_redlines', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('auto_generate_email_drafts', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('theme_preference', sa.String(20), nullable=False, server_default='light'),
        sa.Column('dashboard_layout', postgresql.JSONB, nullable=True),
        sa.Column('integration_settings', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_index('idx_user_settings_ai_model', 'user_settings', ['ai_model_preference'])
    
    # Create unique constraint to ensure one settings record per user
    op.create_unique_constraint('uq_user_settings_user_id', 'user_settings', ['user_id'])


def downgrade():
    """Remove user settings table."""
    op.drop_table('user_settings')