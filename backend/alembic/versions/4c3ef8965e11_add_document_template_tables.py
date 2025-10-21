"""add_document_template_tables

Revision ID: 4c3ef8965e11
Revises: 3b2ef7854d99
Create Date: 2024-10-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4c3ef8965e11'
down_revision = '3b2ef7854d99'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_templates table
    op.create_table('document_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('template_structure', sa.JSON(), nullable=False),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('template_styles', sa.Text(), nullable=True),
        sa.Column('is_system_template', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('parent_template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_template_id'], ['document_templates.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_templates_id'), 'document_templates', ['id'], unique=False)
    op.create_index(op.f('ix_document_templates_template_type'), 'document_templates', ['template_type'], unique=False)
    op.create_index(op.f('ix_document_templates_user_id'), 'document_templates', ['user_id'], unique=False)

    # Create generated_documents table
    op.create_table('generated_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('generation_data', sa.JSON(), nullable=False),
        sa.Column('generated_html', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_format', sa.String(length=20), nullable=False),
        sa.Column('generation_method', sa.String(length=50), nullable=False),
        sa.Column('customization_level', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['document_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_documents_id'), 'generated_documents', ['id'], unique=False)
    op.create_index(op.f('ix_generated_documents_job_id'), 'generated_documents', ['job_id'], unique=False)
    op.create_index(op.f('ix_generated_documents_template_id'), 'generated_documents', ['template_id'], unique=False)
    op.create_index(op.f('ix_generated_documents_user_id'), 'generated_documents', ['user_id'], unique=False)


def downgrade():
    # Drop generated_documents table
    op.drop_index(op.f('ix_generated_documents_user_id'), table_name='generated_documents')
    op.drop_index(op.f('ix_generated_documents_template_id'), table_name='generated_documents')
    op.drop_index(op.f('ix_generated_documents_job_id'), table_name='generated_documents')
    op.drop_index(op.f('ix_generated_documents_id'), table_name='generated_documents')
    op.drop_table('generated_documents')
    
    # Drop document_templates table
    op.drop_index(op.f('ix_document_templates_user_id'), table_name='document_templates')
    op.drop_index(op.f('ix_document_templates_template_type'), table_name='document_templates')
    op.drop_index(op.f('ix_document_templates_id'), table_name='document_templates')
    op.drop_table('document_templates')