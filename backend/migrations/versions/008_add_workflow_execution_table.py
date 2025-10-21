"""Add workflow execution table

Revision ID: 008
Revises: 007
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007_add_jwt_auth_rbac_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add workflow execution table for production orchestration."""
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', sa.String(length=255), nullable=False),
        sa.Column('workflow_type', sa.String(length=100), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.DECIMAL(precision=10, scale=3), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_strategy', sa.String(length=50), nullable=False, server_default='exponential_backoff'),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'], unique=True)
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('idx_workflow_executions_user_id', 'workflow_executions', ['user_id'])
    op.create_index('idx_workflow_executions_created_at', 'workflow_executions', ['created_at'])
    op.create_index('idx_workflow_executions_priority', 'workflow_executions', ['priority'])
    op.create_index('idx_workflow_executions_workflow_type', 'workflow_executions', ['workflow_type'])
    
    # Add trigger for updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_workflow_executions_updated_at
        BEFORE UPDATE ON workflow_executions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    """Remove workflow execution table."""
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_workflow_executions_updated_at ON workflow_executions;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop indexes
    op.drop_index('idx_workflow_executions_workflow_type', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_priority', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_created_at', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_user_id', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_status', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_workflow_id', table_name='workflow_executions')
    
    # Drop table
    op.drop_table('workflow_executions')