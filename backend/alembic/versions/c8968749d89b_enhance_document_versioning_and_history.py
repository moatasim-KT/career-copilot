"""enhance_document_versioning_and_history

Revision ID: c8968749d89b
Revises: 5d4ef9876f22
Create Date: 2025-10-19 12:33:40.177798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8968749d89b'
down_revision: Union[str, Sequence[str], None] = '5d4ef9876f22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced document versioning and history tracking."""
    
    # Create document_history table for tracking all document changes
    op.create_table(
        'document_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),  # created, updated, deleted, restored
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),  # Path to versioned file
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),  # SHA256 checksum for integrity
        sa.Column('created_by', sa.Integer(), nullable=False),  # User who made the change
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('version_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for document_history table
    op.create_index(op.f('ix_document_history_document_id'), 'document_history', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_history_user_id'), 'document_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_history_version_number'), 'document_history', ['version_number'], unique=False)
    op.create_index(op.f('ix_document_history_action'), 'document_history', ['action'], unique=False)
    op.create_index(op.f('ix_document_history_created_at'), 'document_history', ['created_at'], unique=False)
    
    # Composite indexes for efficient queries
    op.create_index('ix_document_history_doc_version', 'document_history', ['document_id', 'version_number'], unique=True)
    op.create_index('ix_document_history_user_created', 'document_history', ['user_id', 'created_at'], unique=False)
    
    # Add new columns to documents table for enhanced versioning
    op.add_column('documents', sa.Column('version_group_id', sa.String(length=36), nullable=True))  # UUID for grouping versions
    op.add_column('documents', sa.Column('checksum', sa.String(length=64), nullable=True))  # SHA256 checksum
    op.add_column('documents', sa.Column('version_notes', sa.Text(), nullable=True))  # Notes about this version
    op.add_column('documents', sa.Column('is_archived', sa.String(length=10), nullable=False, server_default='false'))  # Archive status
    op.add_column('documents', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))  # Archive timestamp
    op.add_column('documents', sa.Column('restored_from_version', sa.Integer(), nullable=True))  # Track if restored from history
    
    # Create index for version group lookups
    op.create_index('ix_documents_version_group', 'documents', ['version_group_id'], unique=False)
    op.create_index('ix_documents_checksum', 'documents', ['checksum'], unique=False)
    op.create_index('ix_documents_archived', 'documents', ['is_archived'], unique=False)
    
    # Create document_version_migrations table for tracking migration strategies
    op.create_table(
        'document_version_migrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('migration_id', sa.String(length=36), nullable=False),  # UUID for migration batch
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('migration_type', sa.String(length=50), nullable=False),  # version_upgrade, compression_migration, etc.
        sa.Column('source_version', sa.String(length=20), nullable=True),
        sa.Column('target_version', sa.String(length=20), nullable=True),
        sa.Column('documents_affected', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),  # pending, running, completed, failed
        sa.Column('progress', sa.Integer(), nullable=False, default=0),  # Progress percentage
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('migration_log', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for document_version_migrations table
    op.create_index(op.f('ix_document_version_migrations_migration_id'), 'document_version_migrations', ['migration_id'], unique=False)
    op.create_index(op.f('ix_document_version_migrations_user_id'), 'document_version_migrations', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_version_migrations_status'), 'document_version_migrations', ['status'], unique=False)
    op.create_index(op.f('ix_document_version_migrations_created_at'), 'document_version_migrations', ['created_at'], unique=False)


def downgrade() -> None:
    """Remove enhanced document versioning and history tracking."""
    
    # Drop new tables
    op.drop_table('document_version_migrations')
    op.drop_table('document_history')
    
    # Remove new columns from documents table
    op.drop_column('documents', 'restored_from_version')
    op.drop_column('documents', 'archived_at')
    op.drop_column('documents', 'is_archived')
    op.drop_column('documents', 'version_notes')
    op.drop_column('documents', 'checksum')
    op.drop_column('documents', 'version_group_id')
