"""Add compression and encryption support

Revision ID: 5d4ef9876f22
Revises: 4c3ef8965e11
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5d4ef9876f22'
down_revision = '4c3ef8965e11'
branch_labels = None
depends_on = None


def upgrade():
    # Add compression and encryption columns to documents table
    op.add_column('documents', sa.Column('is_compressed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('documents', sa.Column('compression_type', sa.String(20), nullable=True))
    op.add_column('documents', sa.Column('compression_ratio', sa.DECIMAL(5, 4), nullable=True))
    op.add_column('documents', sa.Column('original_size', sa.BigInteger(), nullable=True))
    op.add_column('documents', sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('documents', sa.Column('encryption_algorithm', sa.String(20), nullable=True))
    op.add_column('documents', sa.Column('data_hash', sa.String(64), nullable=True))
    
    # Add encryption support to users table for sensitive profile data
    op.add_column('users', sa.Column('profile_encrypted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('settings_encrypted', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add compression and encryption metadata to jobs table for large descriptions
    op.add_column('jobs', sa.Column('description_compressed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('jobs', sa.Column('description_compression_type', sa.String(20), nullable=True))
    op.add_column('jobs', sa.Column('requirements_encrypted', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create indexes for performance
    op.create_index('idx_documents_compressed', 'documents', ['is_compressed'])
    op.create_index('idx_documents_encrypted', 'documents', ['is_encrypted'])
    op.create_index('idx_users_profile_encrypted', 'users', ['profile_encrypted'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_users_profile_encrypted', table_name='users')
    op.drop_index('idx_documents_encrypted', table_name='documents')
    op.drop_index('idx_documents_compressed', table_name='documents')
    
    # Remove columns from jobs table
    op.drop_column('jobs', 'requirements_encrypted')
    op.drop_column('jobs', 'description_compression_type')
    op.drop_column('jobs', 'description_compressed')
    
    # Remove columns from users table
    op.drop_column('users', 'settings_encrypted')
    op.drop_column('users', 'profile_encrypted')
    
    # Remove columns from documents table
    op.drop_column('documents', 'data_hash')
    op.drop_column('documents', 'encryption_algorithm')
    op.drop_column('documents', 'is_encrypted')
    op.drop_column('documents', 'original_size')
    op.drop_column('documents', 'compression_ratio')
    op.drop_column('documents', 'compression_type')
    op.drop_column('documents', 'is_compressed')