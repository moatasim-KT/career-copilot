"""Add vector store tables for contract embeddings and legal precedents

Revision ID: add_vector_store_tables
Revises: 
Create Date: 2024-01-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_vector_store_tables'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    """Add vector store related tables."""
    
    # Contract embeddings table
    op.create_table(
        'contract_embeddings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_analysis_id', sa.String(36), sa.ForeignKey('contract_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('embedding_id', sa.String(255), nullable=False, unique=True),
        
        # Chunk information
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('chunk_text', sa.Text, nullable=False),
        sa.Column('chunk_size', sa.Integer, nullable=False),
        sa.Column('total_chunks', sa.Integer, nullable=False),
        
        # Embedding metadata
        sa.Column('embedding_model', sa.String(100), nullable=False, default='text-embedding-ada-002'),
        sa.Column('processing_time_ms', sa.DECIMAL(10, 3), nullable=True),
        
        # Contract metadata for search optimization
        sa.Column('contract_type', sa.String(100), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('contract_category', sa.String(100), nullable=True),
        
        # Legal context (stored as JSON for SQLite compatibility)
        sa.Column('parties', sa.Text, nullable=True),  # JSON array
        sa.Column('key_terms', sa.Text, nullable=True),  # JSON array
        
        # Additional metadata
        sa.Column('additional_metadata', sa.Text, nullable=True),  # JSON object
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for contract_embeddings
    op.create_index('idx_contract_embeddings_analysis_id', 'contract_embeddings', ['contract_analysis_id'])
    op.create_index('idx_contract_embeddings_embedding_id', 'contract_embeddings', ['embedding_id'])
    op.create_index('idx_contract_embeddings_contract_type', 'contract_embeddings', ['contract_type'])
    op.create_index('idx_contract_embeddings_risk_level', 'contract_embeddings', ['risk_level'])
    op.create_index('idx_contract_embeddings_jurisdiction', 'contract_embeddings', ['jurisdiction'])
    op.create_index('idx_contract_embeddings_category', 'contract_embeddings', ['contract_category'])
    op.create_index('idx_contract_embeddings_chunk_index', 'contract_embeddings', ['chunk_index'])
    op.create_index('idx_contract_embeddings_created_at', 'contract_embeddings', ['created_at'])
    
    # Legal precedents table
    op.create_table(
        'legal_precedents',
        sa.Column('id', sa.String(36), primary_key=True),
        
        # Case information
        sa.Column('case_name', sa.String(500), nullable=False),
        sa.Column('case_number', sa.String(100), nullable=True),
        sa.Column('court', sa.String(200), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=False),
        
        # Case details
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('case_summary', sa.Text, nullable=True),
        sa.Column('legal_principles', sa.Text, nullable=True),  # JSON array
        sa.Column('key_holdings', sa.Text, nullable=True),  # JSON array
        
        # Citation information
        sa.Column('citation', sa.String(200), nullable=True),
        sa.Column('reporter', sa.String(100), nullable=True),
        sa.Column('volume', sa.String(50), nullable=True),
        sa.Column('page', sa.String(50), nullable=True),
        
        # Content
        sa.Column('full_text', sa.Text, nullable=True),
        sa.Column('relevant_excerpts', sa.Text, nullable=True),  # JSON array
        
        # Categorization
        sa.Column('practice_areas', sa.Text, nullable=True),  # JSON array
        sa.Column('legal_topics', sa.Text, nullable=True),  # JSON array
        sa.Column('contract_types', sa.Text, nullable=True),  # JSON array
        
        # Relevance and quality
        sa.Column('relevance_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('authority_level', sa.String(50), nullable=True),
        
        # Source information
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_database', sa.String(100), nullable=True),
        sa.Column('last_verified', sa.DateTime(timezone=True), nullable=True),
        
        # Embedding information
        sa.Column('embedding_id', sa.String(255), nullable=True, unique=True),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        
        # Additional metadata
        sa.Column('additional_metadata', sa.Text, nullable=True),  # JSON object
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for legal_precedents
    op.create_index('idx_legal_precedents_case_name', 'legal_precedents', ['case_name'])
    op.create_index('idx_legal_precedents_jurisdiction', 'legal_precedents', ['jurisdiction'])
    op.create_index('idx_legal_precedents_court', 'legal_precedents', ['court'])
    op.create_index('idx_legal_precedents_decision_date', 'legal_precedents', ['decision_date'])
    op.create_index('idx_legal_precedents_citation', 'legal_precedents', ['citation'])
    op.create_index('idx_legal_precedents_authority_level', 'legal_precedents', ['authority_level'])
    op.create_index('idx_legal_precedents_relevance_score', 'legal_precedents', ['relevance_score'])
    op.create_index('idx_legal_precedents_embedding_id', 'legal_precedents', ['embedding_id'])
    op.create_index('idx_legal_precedents_created_at', 'legal_precedents', ['created_at'])
    
    # Similarity search logs table
    op.create_table(
        'similarity_search_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        
        # Search parameters
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('search_type', sa.String(50), nullable=False),
        sa.Column('similarity_threshold', sa.DECIMAL(3, 2), nullable=False),
        sa.Column('max_results', sa.Integer, nullable=False),
        
        # Filters applied
        sa.Column('metadata_filters', sa.Text, nullable=True),  # JSON object
        sa.Column('contract_types', sa.Text, nullable=True),  # JSON array
        sa.Column('risk_levels', sa.Text, nullable=True),  # JSON array
        sa.Column('jurisdictions', sa.Text, nullable=True),  # JSON array
        
        # Results
        sa.Column('results_count', sa.Integer, nullable=False),
        sa.Column('top_similarity_score', sa.DECIMAL(3, 2), nullable=True),
        
        # Performance metrics
        sa.Column('search_time_ms', sa.DECIMAL(10, 3), nullable=False),
        sa.Column('embedding_time_ms', sa.DECIMAL(10, 3), nullable=True),
        
        # Context
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for similarity_search_logs
    op.create_index('idx_similarity_search_logs_user_id', 'similarity_search_logs', ['user_id'])
    op.create_index('idx_similarity_search_logs_search_type', 'similarity_search_logs', ['search_type'])
    op.create_index('idx_similarity_search_logs_created_at', 'similarity_search_logs', ['created_at'])
    op.create_index('idx_similarity_search_logs_search_time', 'similarity_search_logs', ['search_time_ms'])
    op.create_index('idx_similarity_search_logs_results_count', 'similarity_search_logs', ['results_count'])


def downgrade():
    """Remove vector store related tables."""
    
    # Drop indexes first
    op.drop_index('idx_similarity_search_logs_results_count', 'similarity_search_logs')
    op.drop_index('idx_similarity_search_logs_search_time', 'similarity_search_logs')
    op.drop_index('idx_similarity_search_logs_created_at', 'similarity_search_logs')
    op.drop_index('idx_similarity_search_logs_search_type', 'similarity_search_logs')
    op.drop_index('idx_similarity_search_logs_user_id', 'similarity_search_logs')
    
    op.drop_index('idx_legal_precedents_created_at', 'legal_precedents')
    op.drop_index('idx_legal_precedents_embedding_id', 'legal_precedents')
    op.drop_index('idx_legal_precedents_relevance_score', 'legal_precedents')
    op.drop_index('idx_legal_precedents_authority_level', 'legal_precedents')
    op.drop_index('idx_legal_precedents_citation', 'legal_precedents')
    op.drop_index('idx_legal_precedents_decision_date', 'legal_precedents')
    op.drop_index('idx_legal_precedents_court', 'legal_precedents')
    op.drop_index('idx_legal_precedents_jurisdiction', 'legal_precedents')
    op.drop_index('idx_legal_precedents_case_name', 'legal_precedents')
    
    op.drop_index('idx_contract_embeddings_created_at', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_chunk_index', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_category', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_jurisdiction', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_risk_level', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_contract_type', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_embedding_id', 'contract_embeddings')
    op.drop_index('idx_contract_embeddings_analysis_id', 'contract_embeddings')
    
    # Drop tables
    op.drop_table('similarity_search_logs')
    op.drop_table('legal_precedents')
    op.drop_table('contract_embeddings')