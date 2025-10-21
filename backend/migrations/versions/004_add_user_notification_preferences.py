"""Add user notification preferences table

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add user notification preferences table"""
    
    # Create user_notification_preferences table
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', sa.String(length=100), nullable=False),
        sa.Column('channel_id', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(
        'idx_user_notification_preferences_user_id_type', 
        'user_notification_preferences', 
        ['user_id', 'notification_type']
    )
    op.create_index(
        'idx_user_notification_preferences_user_id', 
        'user_notification_preferences', 
        ['user_id']
    )
    op.create_index(
        'idx_user_notification_preferences_notification_type', 
        'user_notification_preferences', 
        ['notification_type']
    )


def downgrade():
    """Remove user notification preferences table"""
    
    # Drop indexes
    op.drop_index('idx_user_notification_preferences_notification_type', table_name='user_notification_preferences')
    op.drop_index('idx_user_notification_preferences_user_id', table_name='user_notification_preferences')
    op.drop_index('idx_user_notification_preferences_user_id_type', table_name='user_notification_preferences')
    
    # Drop table
    op.drop_table('user_notification_preferences')