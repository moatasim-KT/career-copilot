"""Add DocuSign envelopes and email delivery status tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add DocuSign envelopes and email delivery status tables."""
    
    # Create user_notification_preferences table
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', sa.String(100), nullable=False),
        sa.Column('channel_id', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for user_notification_preferences
    op.create_index('idx_user_notification_preferences_user_id_type', 'user_notification_preferences', ['user_id', 'notification_type'])
    
    # Create docusign_envelopes table
    op.create_table(
        'docusign_envelopes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('envelope_id', sa.String(255), nullable=False),
        sa.Column('contract_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('recipients', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['contract_analysis_id'], ['contract_analyses.id'], ondelete='CASCADE'),
    )
    
    # Create unique constraint and indexes for docusign_envelopes
    op.create_unique_constraint('uq_docusign_envelopes_envelope_id', 'docusign_envelopes', ['envelope_id'])
    op.create_index('idx_docusign_envelopes_envelope_id', 'docusign_envelopes', ['envelope_id'])
    op.create_index('idx_docusign_envelopes_status', 'docusign_envelopes', ['status'])
    op.create_index('idx_docusign_envelopes_contract_analysis_id', 'docusign_envelopes', ['contract_analysis_id'])
    
    # Create email_delivery_statuses table
    op.create_table(
        'email_delivery_statuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for email_delivery_statuses
    op.create_index('idx_email_delivery_statuses_message_id', 'email_delivery_statuses', ['message_id'])
    op.create_index('idx_email_delivery_statuses_recipient', 'email_delivery_statuses', ['recipient'])
    op.create_index('idx_email_delivery_statuses_status', 'email_delivery_statuses', ['status'])
    op.create_index('idx_email_delivery_statuses_sent_at', 'email_delivery_statuses', ['sent_at'])
    
    # Create trigger for docusign_envelopes table
    op.execute("""
        CREATE TRIGGER update_docusign_envelopes_updated_at 
            BEFORE UPDATE ON docusign_envelopes 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop DocuSign envelopes and email delivery status tables."""
    
    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS update_docusign_envelopes_updated_at ON docusign_envelopes;')
    
    # Drop tables in reverse order
    op.drop_table('email_delivery_statuses')
    op.drop_table('docusign_envelopes')
    op.drop_table('user_notification_preferences')