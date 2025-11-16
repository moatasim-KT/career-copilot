"""add calendar tables

Revision ID: 004_add_calendar_tables
Revises: 003_add_analytics_performance_indexes
Create Date: 2025-11-16 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_calendar_tables'
down_revision = '003_add_analytics_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create calendar_credentials table
    op.create_table(
        'calendar_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_credentials_user_id'), 'calendar_credentials', ['user_id'], unique=False)
    
    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=True),
        sa.Column('calendar_credential_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('timezone', sa.String(length=100), default='UTC'),
        sa.Column('reminder_15min', sa.Boolean(), default=True),
        sa.Column('reminder_1hour', sa.Boolean(), default=True),
        sa.Column('reminder_1day', sa.Boolean(), default=False),
        sa.Column('is_synced', sa.Boolean(), default=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
        sa.ForeignKeyConstraint(['calendar_credential_id'], ['calendar_credentials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_calendar_events_application_id'), 'calendar_events', ['application_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_calendar_events_application_id'), table_name='calendar_events')
    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_table('calendar_events')
    op.drop_index(op.f('ix_calendar_credentials_user_id'), table_name='calendar_credentials')
    op.drop_table('calendar_credentials')
