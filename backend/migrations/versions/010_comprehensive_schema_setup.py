"""Comprehensive schema setup with SQLite and PostgreSQL compatibility

Revision ID: 010_comprehensive_schema_setup
Revises: c22e4329ae15
Create Date: 2024-01-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '010_comprehensive_schema_setup'
down_revision = 'c22e4329ae15'
branch_labels = None
depends_on = None


def get_database_type():
    """Determine if we're using PostgreSQL or SQLite."""
    bind = op.get_bind()
    return bind.dialect.name


def upgrade():
    """Create comprehensive database schema with cross-database compatibility."""
    
    db_type = get_database_type()
    
    # PostgreSQL-specific setup
    if db_type == 'postgresql':
        # Create extensions for PostgreSQL
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
        
        # UUID and JSONB types for PostgreSQL
        uuid_type = postgresql.UUID(as_uuid=True)
        jsonb_type = postgresql.JSONB(astext_type=sa.Text())
        array_string_type = postgresql.ARRAY(sa.String())
        inet_type = postgresql.INET()
        uuid_default = sa.text('uuid_generate_v4()')
        
    else:
        # SQLite compatibility types
        uuid_type = sa.String(36)
        jsonb_type = sa.Text()  # Store JSON as text in SQLite
        array_string_type = sa.Text()  # Store arrays as JSON text in SQLite
        inet_type = sa.String(45)  # IPv6 max length
        uuid_default = None  # Will be handled by application code
    
    # Create user_sessions table (missing from current schema)
    op.create_table(
        'user_sessions',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False, unique=True),
        sa.Column('token_family', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('device_info', jsonb_type, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for user_sessions
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'])
    op.create_index('idx_user_sessions_active', 'user_sessions', ['is_active'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    
    # Create role_assignments table
    op.create_table(
        'role_assignments',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('assigned_by', uuid_type, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('context', jsonb_type, nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
    )
    
    # Create indexes for role_assignments
    op.create_index('idx_role_assignments_user_id', 'role_assignments', ['user_id'])
    op.create_index('idx_role_assignments_role', 'role_assignments', ['role'])
    op.create_index('idx_role_assignments_active', 'role_assignments', ['is_active'])
    op.create_index('idx_role_assignments_expires_at', 'role_assignments', ['expires_at'])
    
    # Create permission_grants table
    op.create_table(
        'permission_grants',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission', sa.String(100), nullable=False),
        sa.Column('granted_by', uuid_type, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('conditions', jsonb_type, nullable=True),
    )
    
    # Create indexes for permission_grants
    op.create_index('idx_permission_grants_user_id', 'permission_grants', ['user_id'])
    op.create_index('idx_permission_grants_permission', 'permission_grants', ['permission'])
    op.create_index('idx_permission_grants_active', 'permission_grants', ['is_active'])
    op.create_index('idx_permission_grants_resource', 'permission_grants', ['resource_type', 'resource_id'])
    
    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_category', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource', sa.String(255), nullable=True),
        sa.Column('result', sa.String(20), nullable=True),
        sa.Column('details', jsonb_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for security_events
    op.create_index('idx_security_events_user_id', 'security_events', ['user_id'])
    op.create_index('idx_security_events_type', 'security_events', ['event_type'])
    op.create_index('idx_security_events_category', 'security_events', ['event_category'])
    op.create_index('idx_security_events_severity', 'security_events', ['severity'])
    op.create_index('idx_security_events_created_at', 'security_events', ['created_at'])
    op.create_index('idx_security_events_result', 'security_events', ['result'])
    
    # Create user_notification_preferences table
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notification_type', sa.String(100), nullable=False),
        sa.Column('channel_id', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for user_notification_preferences
    op.create_index('idx_user_notification_preferences_user_id_type', 'user_notification_preferences', ['user_id', 'notification_type'])
    op.create_index('idx_user_notification_preferences_user_id', 'user_notification_preferences', ['user_id'])
    op.create_index('idx_user_notification_preferences_notification_type', 'user_notification_preferences', ['notification_type'])
    
    # Create docusign_envelopes table
    op.create_table(
        'docusign_envelopes',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('envelope_id', sa.String(255), nullable=False, unique=True),
        sa.Column('contract_analysis_id', uuid_type, sa.ForeignKey('contract_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('recipients', jsonb_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for docusign_envelopes
    op.create_index('idx_docusign_envelopes_envelope_id', 'docusign_envelopes', ['envelope_id'])
    op.create_index('idx_docusign_envelopes_contract_analysis_id', 'docusign_envelopes', ['contract_analysis_id'])
    op.create_index('idx_docusign_envelopes_status', 'docusign_envelopes', ['status'])
    
    # Create email_delivery_statuses table
    op.create_table(
        'email_delivery_statuses',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for email_delivery_statuses
    op.create_index('idx_email_delivery_statuses_message_id', 'email_delivery_statuses', ['message_id'])
    op.create_index('idx_email_delivery_statuses_recipient', 'email_delivery_statuses', ['recipient'])
    op.create_index('idx_email_delivery_statuses_status', 'email_delivery_statuses', ['status'])
    
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('ai_model_preference', sa.String(100), nullable=False, default='gpt-3.5-turbo'),
        sa.Column('analysis_depth', sa.String(50), nullable=False, default='normal'),
        sa.Column('email_notifications_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('slack_notifications_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('docusign_notifications_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('risk_threshold_low', sa.DECIMAL(3, 2), nullable=False, default=0.30),
        sa.Column('risk_threshold_medium', sa.DECIMAL(3, 2), nullable=False, default=0.60),
        sa.Column('risk_threshold_high', sa.DECIMAL(3, 2), nullable=False, default=0.80),
        sa.Column('auto_generate_redlines', sa.Boolean, nullable=False, default=True),
        sa.Column('auto_generate_email_drafts', sa.Boolean, nullable=False, default=True),
        sa.Column('preferred_language', sa.String(10), nullable=False, default='en'),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('theme_preference', sa.String(20), nullable=False, default='light'),
        sa.Column('dashboard_layout', jsonb_type, nullable=True),
        sa.Column('integration_settings', jsonb_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for user_settings
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_index('idx_user_settings_ai_model', 'user_settings', ['ai_model_preference'])
    
    # Create similarity_search_logs table
    op.create_table(
        'similarity_search_logs',
        sa.Column('id', uuid_type, primary_key=True, default=uuid_default),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('search_type', sa.String(50), nullable=False),
        sa.Column('similarity_threshold', sa.DECIMAL(3, 2), nullable=False),
        sa.Column('max_results', sa.Integer, nullable=False),
        sa.Column('metadata_filters', jsonb_type, nullable=True),
        sa.Column('contract_types', array_string_type, nullable=True),
        sa.Column('risk_levels', array_string_type, nullable=True),
        sa.Column('jurisdictions', array_string_type, nullable=True),
        sa.Column('results_count', sa.Integer, nullable=False),
        sa.Column('top_similarity_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('search_time_ms', sa.DECIMAL(10, 3), nullable=False),
        sa.Column('embedding_time_ms', sa.DECIMAL(10, 3), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for similarity_search_logs
    op.create_index('idx_similarity_search_logs_user_id', 'similarity_search_logs', ['user_id'])
    op.create_index('idx_similarity_search_logs_search_type', 'similarity_search_logs', ['search_type'])
    op.create_index('idx_similarity_search_logs_created_at', 'similarity_search_logs', ['created_at'])
    op.create_index('idx_similarity_search_logs_search_time', 'similarity_search_logs', ['search_time_ms'])
    op.create_index('idx_similarity_search_logs_results_count', 'similarity_search_logs', ['results_count'])
    
    # PostgreSQL-specific optimizations
    if db_type == 'postgresql':
        # Create function to update updated_at timestamp
        op.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create triggers for tables with updated_at columns
        tables_with_updated_at = ['user_notification_preferences', 'docusign_envelopes', 'user_settings']
        for table in tables_with_updated_at:
            op.execute(f"""
                CREATE TRIGGER update_{table}_updated_at 
                    BEFORE UPDATE ON {table} 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)


def downgrade():
    """Remove comprehensive schema setup."""
    
    db_type = get_database_type()
    
    # Drop triggers and functions for PostgreSQL
    if db_type == 'postgresql':
        tables_with_updated_at = ['user_notification_preferences', 'docusign_envelopes', 'user_settings']
        for table in tables_with_updated_at:
            op.execute(f'DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};')
        
        op.execute('DROP FUNCTION IF EXISTS update_updated_at_column();')
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('similarity_search_logs')
    op.drop_table('user_settings')
    op.drop_table('email_delivery_statuses')
    op.drop_table('docusign_envelopes')
    op.drop_table('user_notification_preferences')
    op.drop_table('security_events')
    op.drop_table('permission_grants')
    op.drop_table('role_assignments')
    op.drop_table('user_sessions')
    
    # Drop PostgreSQL extensions
    if db_type == 'postgresql':
        op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
        op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')