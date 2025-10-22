"""add_resume_parsing_models

Revision ID: df4fbcbf8002
Revises: b6ad015e0d17
Create Date: 2025-10-22 22:14:52.582064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df4fbcbf8002'
down_revision: Union[str, Sequence[str], None] = 'b6ad015e0d17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create resume_uploads table
    op.create_table(
        'resume_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('parsing_status', sa.String(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('extracted_skills', sa.JSON(), nullable=True),
        sa.Column('extracted_experience', sa.String(), nullable=True),
        sa.Column('extracted_contact_info', sa.JSON(), nullable=True),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_uploads_id'), 'resume_uploads', ['id'], unique=False)
    
    # Create content_generations table
    op.create_table(
        'content_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('generated_content', sa.Text(), nullable=False),
        sa.Column('user_modifications', sa.Text(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('template_used', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_generations_id'), 'content_generations', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_content_generations_id'), table_name='content_generations')
    op.drop_table('content_generations')
    op.drop_index(op.f('ix_resume_uploads_id'), table_name='resume_uploads')
    op.drop_table('resume_uploads')
