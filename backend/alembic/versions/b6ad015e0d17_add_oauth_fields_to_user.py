"""add_oauth_fields_to_user

Revision ID: b6ad015e0d17
Revises: e98860839e32
Create Date: 2025-10-22 21:53:52.688354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6ad015e0d17'
down_revision: Union[str, Sequence[str], None] = 'e98860839e32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns already exist to avoid duplicate column errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add OAuth fields to users table if they don't exist
    if 'oauth_provider' not in columns:
        op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
    if 'oauth_id' not in columns:
        op.add_column('users', sa.Column('oauth_id', sa.String(), nullable=True))
    if 'profile_picture_url' not in columns:
        op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))
    
    # Note: SQLite doesn't support ALTER COLUMN to change nullable constraint
    # The hashed_password field will remain NOT NULL in the schema, but we'll handle
    # OAuth users by setting a placeholder value or checking in the application logic


def downgrade() -> None:
    """Downgrade schema."""
    # Remove OAuth fields from users table
    op.drop_column('users', 'profile_picture_url')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
