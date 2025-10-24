"""
Migration to add feedback tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json


def upgrade():
    """Add feedback tables"""
    
    # Create job_recommendation_feedback table
    op.create_table(
        'job_recommendation_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('match_score', sa.Integer(), nullable=True),
        sa.Column('user_skills_at_time', sa.JSON(), nullable=True),
        sa.Column('user_experience_level', sa.String(), nullable=True),
        sa.Column('user_preferred_locations', sa.JSON(), nullable=True),
        sa.Column('job_tech_stack', sa.JSON(), nullable=True),
        sa.Column('job_location', sa.String(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('recommendation_context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for job_recommendation_feedback
    op.create_index('ix_job_recommendation_feedback_id', 'job_recommendation_feedback', ['id'])
    op.create_index('ix_job_recommendation_feedback_user_id', 'job_recommendation_feedback', ['user_id'])
    op.create_index('ix_job_recommendation_feedback_created_at', 'job_recommendation_feedback', ['created_at'])
    
    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('JOB_RECOMMENDATION', 'SKILL_GAP_SUGGESTION', 'CONTENT_GENERATION', 'INTERVIEW_PRACTICE', 'GENERAL', 'BUG_REPORT', 'FEATURE_REQUEST', name='feedbacktype'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='feedbackpriority'), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', name='feedbackstatus'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('screen_resolution', sa.String(length=50), nullable=True),
        sa.Column('browser_info', sa.JSON(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feedback
    op.create_index('ix_feedback_id', 'feedback', ['id'])
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('ix_feedback_type', 'feedback', ['type'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])
    
    # Create feedback_votes table
    op.create_table(
        'feedback_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feedback_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vote', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feedback_votes
    op.create_index('ix_feedback_votes_id', 'feedback_votes', ['id'])
    op.create_index('ix_feedback_votes_feedback_id', 'feedback_votes', ['feedback_id'])
    op.create_index('ix_feedback_votes_user_id', 'feedback_votes', ['user_id'])
    
    # Create onboarding_progress table
    op.create_table(
        'onboarding_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('steps_completed', sa.JSON(), nullable=True),
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('tutorials_completed', sa.JSON(), nullable=True),
        sa.Column('features_discovered', sa.JSON(), nullable=True),
        sa.Column('help_topics_viewed', sa.JSON(), nullable=True),
        sa.Column('show_tooltips', sa.Boolean(), nullable=True),
        sa.Column('show_feature_highlights', sa.Boolean(), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create indexes for onboarding_progress
    op.create_index('ix_onboarding_progress_id', 'onboarding_progress', ['id'])
    op.create_index('ix_onboarding_progress_user_id', 'onboarding_progress', ['user_id'])
    
    # Create help_articles table
    op.create_table(
        'help_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('search_keywords', sa.JSON(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('helpful_votes', sa.Integer(), nullable=True),
        sa.Column('unhelpful_votes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create indexes for help_articles
    op.create_index('ix_help_articles_id', 'help_articles', ['id'])
    op.create_index('ix_help_articles_slug', 'help_articles', ['slug'])
    op.create_index('ix_help_articles_category', 'help_articles', ['category'])
    op.create_index('ix_help_articles_is_published', 'help_articles', ['is_published'])
    op.create_index('ix_help_articles_created_at', 'help_articles', ['created_at'])
    
    # Create help_article_votes table
    op.create_table(
        'help_article_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['help_articles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for help_article_votes
    op.create_index('ix_help_article_votes_id', 'help_article_votes', ['id'])
    op.create_index('ix_help_article_votes_article_id', 'help_article_votes', ['article_id'])
    op.create_index('ix_help_article_votes_user_id', 'help_article_votes', ['user_id'])


def downgrade():
    """Remove feedback tables"""
    
    # Drop tables in reverse order
    op.drop_table('help_article_votes')
    op.drop_table('help_articles')
    op.drop_table('onboarding_progress')
    op.drop_table('feedback_votes')
    op.drop_table('feedback')
    op.drop_table('job_recommendation_feedback')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS feedbacktype')
    op.execute('DROP TYPE IF EXISTS feedbackpriority')
    op.execute('DROP TYPE IF EXISTS feedbackstatus')