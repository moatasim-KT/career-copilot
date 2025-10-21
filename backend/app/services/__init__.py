"""
Services package - Business logic and external service integrations.
"""

from .recommendation_engine import RecommendationEngine

# Import only existing services
# from .document_processor import DocumentProcessingService
# from .vector_store import VectorStoreService, get_vector_store_service
# from .workflow_service import EnhancedWorkflowService

__all__ = [
    "RecommendationEngine",
    # "DocumentProcessingService", 
    # "VectorStoreService",
    # "get_vector_store_service",
    # "EnhancedWorkflowService",
]