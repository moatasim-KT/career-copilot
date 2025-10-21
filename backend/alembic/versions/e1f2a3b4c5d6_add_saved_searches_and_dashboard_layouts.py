"""Add saved searches and dashboard layouts tables

Revision ID: e1f2a3b4c5d6
Revises: d9f8e7c6b5a4
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd9f8e7c6b5a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create saved_searches table
    op.create_table('saved_searches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_searches_id'), 'saved_searches', ['id'], unique=False)
    
    # Create dashboard_layouts table
    op.create_table('dashboard_layouts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('widgets', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_layouts_id'), 'dashboard_layouts', ['id'], unique=False)


def downgrade() -> None:
    # Drop dashboard_layouts table
    op.drop_index(op.f('ix_dashboard_layouts_id'), table_name='dashboard_layouts')
    op.drop_table('dashboard_layouts')
    
    # Drop saved_searches table
    op.drop_index(op.f('ix_saved_searches_id'), table_name='saved_searches')
    op.drop_table('saved_searches')