"""Add feedback and onboarding tables

Revision ID: d9f8e7c6b5a4
Revises: c8968749d89b
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd9f8e7c6b5a4'
down_revision = 'c8968749d89b'
branch_labels = None
depends_on = None


def upgrade():
    # Create feedback table
    op.create_table('feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('BUG_REPORT', 'FEATURE_REQUEST', 'GENERAL_FEEDBACK', 'USABILITY_ISSUE', 'PERFORMANCE_ISSUE', name='feedbacktype'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='feedbackpriority'), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'DUPLICATE', name='feedbackstatus'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('screen_resolution', sa.String(length=50), nullable=True),
        sa.Column('browser_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)

    # Create feedback_votes table
    op.create_table('feedback_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('feedback_id', sa.Integer(), nullable=False),
        sa.Column('vote', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_votes_id'), 'feedback_votes', ['id'], unique=False)

    # Create onboarding_progress table
    op.create_table('onboarding_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('steps_completed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('tutorials_completed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('features_discovered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('help_topics_viewed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('show_tooltips', sa.Boolean(), nullable=True),
        sa.Column('show_feature_highlights', sa.Boolean(), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_onboarding_progress_id'), 'onboarding_progress', ['id'], unique=False)

    # Create help_articles table
    op.create_table('help_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('helpful_votes', sa.Integer(), nullable=True),
        sa.Column('unhelpful_votes', sa.Integer(), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('search_keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_help_articles_id'), 'help_articles', ['id'], unique=False)
    op.create_index(op.f('ix_help_articles_slug'), 'help_articles', ['slug'], unique=True)

    # Create help_article_votes table
    op.create_table('help_article_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['help_articles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_help_article_votes_id'), 'help_article_votes', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_help_article_votes_id'), table_name='help_article_votes')
    op.drop_table('help_article_votes')
    
    op.drop_index(op.f('ix_help_articles_slug'), table_name='help_articles')
    op.drop_index(op.f('ix_help_articles_id'), table_name='help_articles')
    op.drop_table('help_articles')
    
    op.drop_index(op.f('ix_onboarding_progress_id'), table_name='onboarding_progress')
    op.drop_table('onboarding_progress')
    
    op.drop_index(op.f('ix_feedback_votes_id'), table_name='feedback_votes')
    op.drop_table('feedback_votes')
    
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS feedbackstatus')
    op.execute('DROP TYPE IF EXISTS feedbackpriority')
    op.execute('DROP TYPE IF EXISTS feedbacktype')