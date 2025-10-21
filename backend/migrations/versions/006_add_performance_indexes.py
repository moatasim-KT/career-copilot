"""Add performance optimization indexes (SQLite compatible)

Revision ID: 006_sqlite
Revises: 005
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance optimization indexes (SQLite compatible)."""
    
    # Basic indexes for common query patterns (SQLite compatible)
    
    # Contract analyses performance indexes
    try:
        op.create_index(
            'idx_contract_analyses_user_status_created',
            'contract_analyses',
            ['user_id', 'analysis_status', 'created_at']
        )
    except Exception:
        pass  # Index may already exist
    
    try:
        op.create_index(
            'idx_contract_analyses_status_created',
            'contract_analyses',
            ['analysis_status', 'created_at']
        )
    except Exception:
        pass
    
    try:
        op.create_index(
            'idx_contract_analyses_risk_score',
            'contract_analyses',
            ['risk_score']
        )
    except Exception:
        pass
    
    try:
        op.create_index(
            'idx_contract_analyses_completed_at',
            'contract_analyses',
            ['completed_at']
        )
    except Exception:
        pass
    
    # File hash index for duplicate detection
    try:
        op.create_index(
            'idx_contract_analyses_file_hash_user',
            'contract_analyses',
            ['file_hash', 'user_id']
        )
    except Exception:
        pass
    
    # User management performance indexes
    try:
        op.create_index(
            'idx_users_active_created',
            'users',
            ['is_active', 'created_at']
        )
    except Exception:
        pass
    
    # API keys performance indexes
    try:
        op.create_index(
            'idx_api_keys_user_active',
            'api_keys',
            ['user_id', 'is_active']
        )
    except Exception:
        pass
    
    try:
        op.create_index(
            'idx_api_keys_expires_at',
            'api_keys',
            ['expires_at']
        )
    except Exception:
        pass
    
    # Audit logs performance indexes
    try:
        op.create_index(
            'idx_audit_logs_user_event_created',
            'audit_logs',
            ['user_id', 'event_type', 'created_at']
        )
    except Exception:
        pass
    
    try:
        op.create_index(
            'idx_audit_logs_created',
            'audit_logs',
            ['created_at']
        )
    except Exception:
        pass
    
    # Basic indexes for JSON columns (SQLite compatible)
    try:
        op.create_index(
            'idx_contract_analyses_filename',
            'contract_analyses',
            ['filename']
        )
    except Exception:
        pass
    
    # Statistics views (SQLite compatible)
    try:
        op.execute("""
            CREATE VIEW IF NOT EXISTS contract_analysis_stats AS
            SELECT 
                analysis_status,
                COUNT(*) as count,
                AVG(processing_time_seconds) as avg_processing_time,
                AVG(risk_score) as avg_risk_score,
                MIN(created_at) as first_analysis,
                MAX(created_at) as last_analysis
            FROM contract_analyses 
            GROUP BY analysis_status
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            CREATE VIEW IF NOT EXISTS user_activity_stats AS
            SELECT 
                u.id,
                u.username,
                u.email,
                COUNT(ca.id) as total_analyses,
                COUNT(CASE WHEN ca.analysis_status = 'completed' THEN 1 END) as completed_analyses,
                AVG(ca.risk_score) as avg_risk_score,
                MAX(ca.created_at) as last_analysis_date
            FROM users u
            LEFT JOIN contract_analyses ca ON u.id = ca.user_id
            WHERE u.is_active = 1
            GROUP BY u.id, u.username, u.email
        """)
    except Exception:
        pass


def downgrade() -> None:
    """Remove performance optimization indexes."""
    
    # Drop views
    try:
        op.execute('DROP VIEW IF EXISTS user_activity_stats')
        op.execute('DROP VIEW IF EXISTS contract_analysis_stats')
    except Exception:
        pass
    
    # Drop indexes (in reverse order)
    indexes_to_drop = [
        'idx_contract_analyses_filename',
        'idx_audit_logs_created',
        'idx_audit_logs_user_event_created',
        'idx_api_keys_expires_at',
        'idx_api_keys_user_active',
        'idx_users_active_created',
        'idx_contract_analyses_file_hash_user',
        'idx_contract_analyses_completed_at',
        'idx_contract_analyses_risk_score',
        'idx_contract_analyses_status_created',
        'idx_contract_analyses_user_status_created'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name)
        except Exception:
            pass  # Index may not exist