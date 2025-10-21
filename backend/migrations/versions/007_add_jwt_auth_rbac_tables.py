"""Add JWT authentication and RBAC tables

Revision ID: 007_add_jwt_auth_rbac_tables
Revises: 006_add_performance_indexes
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_jwt_auth_rbac_tables'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add JWT authentication and RBAC tables."""
    
    # Add new columns to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('roles', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'))
    op.add_column('users', sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'))
    op.add_column('users', sa.Column('security_level', sa.String(20), nullable=False, server_default='standard'))
    
    # MFA fields
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('mfa_secret', sa.String(32), nullable=True))
    op.add_column('users', sa.Column('backup_codes', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Session and login tracking
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_ip', sa.String(45), nullable=True))
    op.add_column('users', sa.Column('last_login_user_agent', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Account status
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True))
    
    # Copy hashed_password to password_hash for existing users
    op.execute("UPDATE users SET password_hash = hashed_password WHERE hashed_password IS NOT NULL")
    
    # Make password_hash not nullable
    op.alter_column('users', 'password_hash', nullable=False)
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('token_family', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create role_assignments table
    op.create_table('role_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create permission_grants table
    op.create_table('permission_grants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission', sa.String(100), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create security_events table
    op.create_table('security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_category', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource', sa.String(255), nullable=True),
        sa.Column('result', sa.String(20), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_roles', 'users', ['roles'])
    op.create_index('idx_users_security_level', 'users', ['security_level'])
    op.create_index('idx_users_mfa_enabled', 'users', ['mfa_enabled'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    
    # Create indexes for user_sessions table
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'])
    op.create_index('idx_user_sessions_active', 'user_sessions', ['is_active'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    
    # Create indexes for role_assignments table
    op.create_index('idx_role_assignments_user_id', 'role_assignments', ['user_id'])
    op.create_index('idx_role_assignments_role', 'role_assignments', ['role'])
    op.create_index('idx_role_assignments_active', 'role_assignments', ['is_active'])
    op.create_index('idx_role_assignments_expires_at', 'role_assignments', ['expires_at'])
    
    # Create indexes for permission_grants table
    op.create_index('idx_permission_grants_user_id', 'permission_grants', ['user_id'])
    op.create_index('idx_permission_grants_permission', 'permission_grants', ['permission'])
    op.create_index('idx_permission_grants_active', 'permission_grants', ['is_active'])
    op.create_index('idx_permission_grants_resource', 'permission_grants', ['resource_type', 'resource_id'])
    
    # Create indexes for security_events table
    op.create_index('idx_security_events_user_id', 'security_events', ['user_id'])
    op.create_index('idx_security_events_type', 'security_events', ['event_type'])
    op.create_index('idx_security_events_category', 'security_events', ['event_category'])
    op.create_index('idx_security_events_severity', 'security_events', ['severity'])
    op.create_index('idx_security_events_created_at', 'security_events', ['created_at'])
    op.create_index('idx_security_events_result', 'security_events', ['result'])


def downgrade():
    """Remove JWT authentication and RBAC tables."""
    
    # Drop indexes for security_events table
    op.drop_index('idx_security_events_result', table_name='security_events')
    op.drop_index('idx_security_events_created_at', table_name='security_events')
    op.drop_index('idx_security_events_severity', table_name='security_events')
    op.drop_index('idx_security_events_category', table_name='security_events')
    op.drop_index('idx_security_events_type', table_name='security_events')
    op.drop_index('idx_security_events_user_id', table_name='security_events')
    
    # Drop indexes for permission_grants table
    op.drop_index('idx_permission_grants_resource', table_name='permission_grants')
    op.drop_index('idx_permission_grants_active', table_name='permission_grants')
    op.drop_index('idx_permission_grants_permission', table_name='permission_grants')
    op.drop_index('idx_permission_grants_user_id', table_name='permission_grants')
    
    # Drop indexes for role_assignments table
    op.drop_index('idx_role_assignments_expires_at', table_name='role_assignments')
    op.drop_index('idx_role_assignments_active', table_name='role_assignments')
    op.drop_index('idx_role_assignments_role', table_name='role_assignments')
    op.drop_index('idx_role_assignments_user_id', table_name='role_assignments')
    
    # Drop indexes for user_sessions table
    op.drop_index('idx_user_sessions_expires_at', table_name='user_sessions')
    op.drop_index('idx_user_sessions_active', table_name='user_sessions')
    op.drop_index('idx_user_sessions_session_id', table_name='user_sessions')
    op.drop_index('idx_user_sessions_user_id', table_name='user_sessions')
    
    # Drop indexes for users table
    op.drop_index('idx_users_last_login', table_name='users')
    op.drop_index('idx_users_mfa_enabled', table_name='users')
    op.drop_index('idx_users_security_level', table_name='users')
    op.drop_index('idx_users_roles', table_name='users')
    
    # Drop tables
    op.drop_table('security_events')
    op.drop_table('permission_grants')
    op.drop_table('role_assignments')
    op.drop_table('user_sessions')
    
    # Remove columns from users table
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'last_login_user_agent')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'security_level')
    op.drop_column('users', 'permissions')
    op.drop_column('users', 'roles')
    op.drop_column('users', 'password_hash')