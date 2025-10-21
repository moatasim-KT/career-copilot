"""Add advanced workflow management tables

Revision ID: 009
Revises: 008
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """Add advanced workflow management tables."""
    
    # Create workflow_audit_logs table
    op.create_table(
        'workflow_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', sa.String(length=255), nullable=False),
        sa.Column('execution_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('compliance_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for workflow_audit_logs
    op.create_index('idx_workflow_audit_logs_workflow_id', 'workflow_audit_logs', ['workflow_id'])
    op.create_index('idx_workflow_audit_logs_execution_id', 'workflow_audit_logs', ['execution_id'])
    op.create_index('idx_workflow_audit_logs_event_type', 'workflow_audit_logs', ['event_type'])
    op.create_index('idx_workflow_audit_logs_timestamp', 'workflow_audit_logs', ['timestamp'])
    op.create_index('idx_workflow_audit_logs_user_id', 'workflow_audit_logs', ['user_id'])
    
    # Create workflow_templates table
    op.create_table(
        'workflow_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=100), nullable=False),
        sa.Column('execution_mode', sa.String(length=50), nullable=False),
        sa.Column('template_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for workflow_templates
    op.create_index('idx_workflow_templates_template_id', 'workflow_templates', ['template_id'], unique=True)
    op.create_index('idx_workflow_templates_template_type', 'workflow_templates', ['template_type'])
    op.create_index('idx_workflow_templates_is_active', 'workflow_templates', ['is_active'])
    
    # Create workflow_schedules table
    op.create_table(
        'workflow_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_id', sa.String(length=255), nullable=False),
        sa.Column('workflow_template_id', sa.String(length=255), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False),
        sa.Column('schedule_expression', sa.String(length=255), nullable=False),
        sa.Column('schedule_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('next_execution', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_execution', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_executions', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for workflow_schedules
    op.create_index('idx_workflow_schedules_schedule_id', 'workflow_schedules', ['schedule_id'], unique=True)
    op.create_index('idx_workflow_schedules_template_id', 'workflow_schedules', ['workflow_template_id'])
    op.create_index('idx_workflow_schedules_next_execution', 'workflow_schedules', ['next_execution'])
    op.create_index('idx_workflow_schedules_enabled', 'workflow_schedules', ['enabled'])
    
    # Add trigger for updated_at timestamp on workflow_templates
    op.execute("""
        CREATE TRIGGER update_workflow_templates_updated_at
        BEFORE UPDATE ON workflow_templates
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Add trigger for updated_at timestamp on workflow_schedules
    op.execute("""
        CREATE TRIGGER update_workflow_schedules_updated_at
        BEFORE UPDATE ON workflow_schedules
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    """Remove advanced workflow management tables."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_workflow_schedules_updated_at ON workflow_schedules;")
    op.execute("DROP TRIGGER IF EXISTS update_workflow_templates_updated_at ON workflow_templates;")
    
    # Drop workflow_schedules table
    op.drop_index('idx_workflow_schedules_enabled', table_name='workflow_schedules')
    op.drop_index('idx_workflow_schedules_next_execution', table_name='workflow_schedules')
    op.drop_index('idx_workflow_schedules_template_id', table_name='workflow_schedules')
    op.drop_index('idx_workflow_schedules_schedule_id', table_name='workflow_schedules')
    op.drop_table('workflow_schedules')
    
    # Drop workflow_templates table
    op.drop_index('idx_workflow_templates_is_active', table_name='workflow_templates')
    op.drop_index('idx_workflow_templates_template_type', table_name='workflow_templates')
    op.drop_index('idx_workflow_templates_template_id', table_name='workflow_templates')
    op.drop_table('workflow_templates')
    
    # Drop workflow_audit_logs table
    op.drop_index('idx_workflow_audit_logs_user_id', table_name='workflow_audit_logs')
    op.drop_index('idx_workflow_audit_logs_timestamp', table_name='workflow_audit_logs')
    op.drop_index('idx_workflow_audit_logs_event_type', table_name='workflow_audit_logs')
    op.drop_index('idx_workflow_audit_logs_execution_id', table_name='workflow_audit_logs')
    op.drop_index('idx_workflow_audit_logs_workflow_id', table_name='workflow_audit_logs')
    op.drop_table('workflow_audit_logs')