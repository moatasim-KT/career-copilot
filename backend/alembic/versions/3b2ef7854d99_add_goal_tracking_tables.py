"""Add goal tracking tables

Revision ID: 3b2ef7854d99
Revises: 2a1db6753c88
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3b2ef7854d99'
down_revision = '2a1db6753c88'
branch_labels = None
depends_on = None


def upgrade():
    # Create goals table
    op.create_table('goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('current_value', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('goal_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_id'), 'goals', ['id'], unique=False)
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'], unique=False)
    op.create_index(op.f('ix_goals_goal_type'), 'goals', ['goal_type'], unique=False)

    # Create goal_progress table
    op.create_table('goal_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('progress_date', sa.Date(), nullable=False),
        sa.Column('value_added', sa.Integer(), nullable=False),
        sa.Column('total_value', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_progress_id'), 'goal_progress', ['id'], unique=False)
    op.create_index(op.f('ix_goal_progress_goal_id'), 'goal_progress', ['goal_id'], unique=False)
    op.create_index(op.f('ix_goal_progress_progress_date'), 'goal_progress', ['progress_date'], unique=False)

    # Create milestones table
    op.create_table('milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('milestone_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('achievement_value', sa.Integer(), nullable=True),
        sa.Column('achievement_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('milestone_metadata', sa.JSON(), nullable=False),
        sa.Column('is_celebrated', sa.Boolean(), nullable=False),
        sa.Column('celebrated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_id'), 'milestones', ['id'], unique=False)
    op.create_index(op.f('ix_milestones_user_id'), 'milestones', ['user_id'], unique=False)
    op.create_index(op.f('ix_milestones_milestone_type'), 'milestones', ['milestone_type'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_milestones_milestone_type'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_user_id'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_id'), table_name='milestones')
    op.drop_table('milestones')
    
    op.drop_index(op.f('ix_goal_progress_progress_date'), table_name='goal_progress')
    op.drop_index(op.f('ix_goal_progress_goal_id'), table_name='goal_progress')
    op.drop_index(op.f('ix_goal_progress_id'), table_name='goal_progress')
    op.drop_table('goal_progress')
    
    op.drop_index(op.f('ix_goals_goal_type'), table_name='goals')
    op.drop_index(op.f('ix_goals_user_id'), table_name='goals')
    op.drop_index(op.f('ix_goals_id'), table_name='goals')
    op.drop_table('goals')