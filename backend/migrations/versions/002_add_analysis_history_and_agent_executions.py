"""Add analysis history and agent executions tables for audit trail and performance tracking

Revision ID: 002_add_analysis_history_and_agent_executions
Revises: add_vector_store_tables
Create Date: 2024-01-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_analysis_history_and_agent_executions'
down_revision = '001_create_base_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add analysis history and agent executions tables."""
    
    # Analysis History Table for audit trail
    op.create_table(
        'analysis_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('contract_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('risk_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('processing_time', sa.DECIMAL(10, 3), nullable=True),
        
        # Results and metadata
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('risky_clauses_count', sa.Integer, nullable=True, default=0),
        sa.Column('recommendations_count', sa.Integer, nullable=True, default=0),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('total_tokens', sa.Integer, nullable=True),
        sa.Column('total_cost', sa.DECIMAL(10, 4), nullable=True),
        
        # Agent tracking
        sa.Column('completed_agents', sa.Text, nullable=True),  # JSON array
        sa.Column('failed_agents', sa.Text, nullable=True),  # JSON array
        sa.Column('agent_count', sa.Integer, nullable=True, default=0),
        
        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, default=0),
        sa.Column('fallback_used', sa.Boolean, nullable=False, default=False),
        
        # Additional metadata
        sa.Column('analysis_metadata', sa.Text, nullable=True),  # JSON object
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        # Soft delete for audit trail
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for analysis_history
    op.create_index('idx_analysis_history_contract_id', 'analysis_history', ['contract_id'])
    op.create_index('idx_analysis_history_analysis_type', 'analysis_history', ['analysis_type'])
    op.create_index('idx_analysis_history_status', 'analysis_history', ['status'])
    op.create_index('idx_analysis_history_risk_score', 'analysis_history', ['risk_score'])
    op.create_index('idx_analysis_history_risk_level', 'analysis_history', ['risk_level'])
    op.create_index('idx_analysis_history_model_used', 'analysis_history', ['model_used'])
    op.create_index('idx_analysis_history_created_at', 'analysis_history', ['created_at'])
    op.create_index('idx_analysis_history_completed_at', 'analysis_history', ['completed_at'])
    op.create_index('idx_analysis_history_processing_time', 'analysis_history', ['processing_time'])
    op.create_index('idx_analysis_history_total_cost', 'analysis_history', ['total_cost'])
    op.create_index('idx_analysis_history_deleted_at', 'analysis_history', ['deleted_at'])
    
    # Composite indexes for common queries
    op.create_index('idx_analysis_history_contract_status', 'analysis_history', ['contract_id', 'status'])
    op.create_index('idx_analysis_history_type_created', 'analysis_history', ['analysis_type', 'created_at'])
    op.create_index('idx_analysis_history_status_created', 'analysis_history', ['status', 'created_at'])
    
    # Agent Executions Table for performance tracking
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('analysis_history.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        
        # Performance metrics
        sa.Column('execution_time', sa.DECIMAL(10, 3), nullable=True),
        sa.Column('token_usage', sa.Integer, nullable=True),
        sa.Column('cost', sa.DECIMAL(10, 4), nullable=True),
        
        # LLM provider information
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer, nullable=True),
        sa.Column('completion_tokens', sa.Integer, nullable=True),
        
        # Error handling and retry information
        sa.Column('retry_count', sa.Integer, nullable=False, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('fallback_used', sa.Boolean, nullable=False, default=False),
        sa.Column('fallback_provider', sa.String(50), nullable=True),
        
        # Circuit breaker information
        sa.Column('circuit_breaker_triggered', sa.Boolean, nullable=False, default=False),
        sa.Column('circuit_breaker_state', sa.String(20), nullable=True),
        
        # Request correlation
        sa.Column('correlation_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        
        # Result information
        sa.Column('result_size_bytes', sa.Integer, nullable=True),
        sa.Column('result_quality_score', sa.DECIMAL(3, 2), nullable=True),
        
        # Additional metadata
        sa.Column('execution_metadata', sa.Text, nullable=True),  # JSON object
        
        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for agent_executions
    op.create_index('idx_agent_executions_analysis_id', 'agent_executions', ['analysis_id'])
    op.create_index('idx_agent_executions_agent_name', 'agent_executions', ['agent_name'])
    op.create_index('idx_agent_executions_agent_type', 'agent_executions', ['agent_type'])
    op.create_index('idx_agent_executions_status', 'agent_executions', ['status'])
    op.create_index('idx_agent_executions_llm_provider', 'agent_executions', ['llm_provider'])
    op.create_index('idx_agent_executions_model_name', 'agent_executions', ['model_name'])
    op.create_index('idx_agent_executions_execution_time', 'agent_executions', ['execution_time'])
    op.create_index('idx_agent_executions_token_usage', 'agent_executions', ['token_usage'])
    op.create_index('idx_agent_executions_cost', 'agent_executions', ['cost'])
    op.create_index('idx_agent_executions_error_type', 'agent_executions', ['error_type'])
    op.create_index('idx_agent_executions_correlation_id', 'agent_executions', ['correlation_id'])
    op.create_index('idx_agent_executions_started_at', 'agent_executions', ['started_at'])
    op.create_index('idx_agent_executions_completed_at', 'agent_executions', ['completed_at'])
    op.create_index('idx_agent_executions_created_at', 'agent_executions', ['created_at'])
    
    # Composite indexes for performance analysis
    op.create_index('idx_agent_executions_analysis_agent', 'agent_executions', ['analysis_id', 'agent_name'])
    op.create_index('idx_agent_executions_agent_status', 'agent_executions', ['agent_name', 'status'])
    op.create_index('idx_agent_executions_provider_model', 'agent_executions', ['llm_provider', 'model_name'])
    op.create_index('idx_agent_executions_status_started', 'agent_executions', ['status', 'started_at'])
    op.create_index('idx_agent_executions_agent_time', 'agent_executions', ['agent_name', 'execution_time'])
    op.create_index('idx_agent_executions_provider_cost', 'agent_executions', ['llm_provider', 'cost'])
    
    # Performance monitoring indexes
    op.create_index('idx_agent_executions_perf_monitoring', 'agent_executions', 
                   ['agent_name', 'status', 'started_at', 'execution_time'])
    op.create_index('idx_agent_executions_cost_analysis', 'agent_executions', 
                   ['llm_provider', 'model_name', 'cost', 'token_usage'])
    op.create_index('idx_agent_executions_error_analysis', 'agent_executions', 
                   ['error_type', 'agent_name', 'retry_count', 'started_at'])


def downgrade():
    """Remove analysis history and agent executions tables."""
    
    # Drop indexes first for agent_executions
    op.drop_index('idx_agent_executions_error_analysis', 'agent_executions')
    op.drop_index('idx_agent_executions_cost_analysis', 'agent_executions')
    op.drop_index('idx_agent_executions_perf_monitoring', 'agent_executions')
    op.drop_index('idx_agent_executions_provider_cost', 'agent_executions')
    op.drop_index('idx_agent_executions_agent_time', 'agent_executions')
    op.drop_index('idx_agent_executions_status_started', 'agent_executions')
    op.drop_index('idx_agent_executions_provider_model', 'agent_executions')
    op.drop_index('idx_agent_executions_agent_status', 'agent_executions')
    op.drop_index('idx_agent_executions_analysis_agent', 'agent_executions')
    op.drop_index('idx_agent_executions_created_at', 'agent_executions')
    op.drop_index('idx_agent_executions_completed_at', 'agent_executions')
    op.drop_index('idx_agent_executions_started_at', 'agent_executions')
    op.drop_index('idx_agent_executions_correlation_id', 'agent_executions')
    op.drop_index('idx_agent_executions_error_type', 'agent_executions')
    op.drop_index('idx_agent_executions_cost', 'agent_executions')
    op.drop_index('idx_agent_executions_token_usage', 'agent_executions')
    op.drop_index('idx_agent_executions_execution_time', 'agent_executions')
    op.drop_index('idx_agent_executions_model_name', 'agent_executions')
    op.drop_index('idx_agent_executions_llm_provider', 'agent_executions')
    op.drop_index('idx_agent_executions_status', 'agent_executions')
    op.drop_index('idx_agent_executions_agent_type', 'agent_executions')
    op.drop_index('idx_agent_executions_agent_name', 'agent_executions')
    op.drop_index('idx_agent_executions_analysis_id', 'agent_executions')
    
    # Drop indexes for analysis_history
    op.drop_index('idx_analysis_history_status_created', 'analysis_history')
    op.drop_index('idx_analysis_history_type_created', 'analysis_history')
    op.drop_index('idx_analysis_history_contract_status', 'analysis_history')
    op.drop_index('idx_analysis_history_deleted_at', 'analysis_history')
    op.drop_index('idx_analysis_history_total_cost', 'analysis_history')
    op.drop_index('idx_analysis_history_processing_time', 'analysis_history')
    op.drop_index('idx_analysis_history_completed_at', 'analysis_history')
    op.drop_index('idx_analysis_history_created_at', 'analysis_history')
    op.drop_index('idx_analysis_history_model_used', 'analysis_history')
    op.drop_index('idx_analysis_history_risk_level', 'analysis_history')
    op.drop_index('idx_analysis_history_risk_score', 'analysis_history')
    op.drop_index('idx_analysis_history_status', 'analysis_history')
    op.drop_index('idx_analysis_history_analysis_type', 'analysis_history')
    op.drop_index('idx_analysis_history_contract_id', 'analysis_history')
    
    # Drop tables
    op.drop_table('agent_executions')
    op.drop_table('analysis_history')