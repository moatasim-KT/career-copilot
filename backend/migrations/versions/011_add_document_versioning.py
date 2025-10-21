"""
Add document versioning tables.

Revision ID: 011
Revises: 010
Create Date: 2024-01-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """Add document versioning tables."""
    
    # Document versions table
    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Index('idx_document_versions_document_id', 'document_id'),
        sa.Index('idx_document_versions_status', 'status'),
        sa.Index('idx_document_versions_created_at', 'created_at')
    )
    
    # Version history table
    op.create_table(
        'version_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('version_id', sa.String(36), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('performed_by', sa.String(36), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('changes', sa.JSON, nullable=True),
        sa.Index('idx_version_history_version_id', 'version_id'),
        sa.Index('idx_version_history_action', 'action'),
        sa.Index('idx_version_history_performed_at', 'performed_at')
    )


def downgrade():
    """Remove document versioning tables."""
    op.drop_table('version_history')
    op.drop_table('document_versions')
