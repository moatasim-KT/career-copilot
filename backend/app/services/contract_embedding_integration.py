"""
Contract Embedding Integration Service.

This service integrates the vector store with the job application tracking workflow,
automatically generating and storing embeddings when contracts are analyzed.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..core.logging import get_logger
from ..models.database_models import ContractAnalysis
from ..repositories.contract_embedding_repository import ContractEmbeddingRepository
from ..services.vector_store_service import get_vector_store_service, VectorStoreService
from ..core.database import get_db_session

logger = get_logger(__name__)


class ContractEmbeddingIntegrationService:
    """Service for integrating contract embeddings with the analysis workflow."""
    
    def __init__(self):
        self.vector_store: Optional[VectorStoreService] = None
    
    async def initialize(self):
        """Initialize the integration service."""
        if self.vector_store is None:
            self.vector_store = await get_vector_store_service()
        logger.info("Contract embedding integration service initialized")
    
    async def process_contract_analysis(
        self,
        contract_analysis: ContractAnalysis,
        generate_embeddings: bool = True,
        store_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Process a job application tracking to generate and store embeddings.
        
        Args:
            contract_analysis: The job application tracking object
            generate_embeddings: Whether to generate vector embeddings
            store_metadata: Whether to store embedding metadata in database
            
        Returns:
            Dict containing processing results and statistics
        """
        if not self.vector_store:
            await self.initialize()
        
        try:
            logger.info(f"Processing job application tracking {contract_analysis.id} for embeddings")
            
            # Extract contract information
            contract_text = contract_analysis.contract_text or ""
            if not contract_text.strip():
                logger.warning(f"No contract text found for analysis {contract_analysis.id}")
                return {
                    "success": False,
                    "error": "No contract text available",
                    "embeddings_generated": 0
                }
            
            # Prepare metadata
            metadata = self._prepare_contract_metadata(contract_analysis)
            
            # Generate and store embeddings
            embeddings = []
            if generate_embeddings:
                embeddings = await self.vector_store.store_contract_embeddings(
                    contract_id=str(contract_analysis.id),
                    contract_text=contract_text,
                    metadata=metadata
                )
            
            # Store embedding metadata in database
            embedding_records = []
            if store_metadata and embeddings:
                embedding_records = await self._store_embedding_metadata(
                    contract_analysis, embeddings
                )
            
            result = {
                "success": True,
                "contract_analysis_id": str(contract_analysis.id),
                "embeddings_generated": len(embeddings),
                "metadata_records_created": len(embedding_records),
                "processing_time": datetime.utcnow().isoformat(),
                "metadata": metadata
            }
            
            logger.info(f"Successfully processed job application tracking {contract_analysis.id}: {len(embeddings)} embeddings generated")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process job application tracking {contract_analysis.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "contract_analysis_id": str(contract_analysis.id),
                "embeddings_generated": 0
            }
    
    async def batch_process_contracts(
        self,
        contract_analyses: List[ContractAnalysis],
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Process multiple contract analyses in batches.
        
        Args:
            contract_analyses: List of job application tracking objects
            batch_size: Number of contracts to process concurrently
            
        Returns:
            Dict containing batch processing results
        """
        if not self.vector_store:
            await self.initialize()
        
        logger.info(f"Starting batch processing of {len(contract_analyses)} contracts")
        
        total_contracts = len(contract_analyses)
        processed_contracts = 0
        failed_contracts = 0
        total_embeddings = 0
        errors = []
        
        # Process contracts in batches
        for i in range(0, total_contracts, batch_size):
            batch = contract_analyses[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.process_contract_analysis(contract)
                for contract in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process batch results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    failed_contracts += 1
                    errors.append({
                        "contract_analysis_id": str(batch[j].id),
                        "error": str(result)
                    })
                elif result.get("success"):
                    processed_contracts += 1
                    total_embeddings += result.get("embeddings_generated", 0)
                else:
                    failed_contracts += 1
                    errors.append({
                        "contract_analysis_id": result.get("contract_analysis_id", "unknown"),
                        "error": result.get("error", "Unknown error")
                    })
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_contracts + batch_size - 1) // batch_size}")
        
        result = {
            "total_contracts": total_contracts,
            "processed_contracts": processed_contracts,
            "failed_contracts": failed_contracts,
            "total_embeddings": total_embeddings,
            "success_rate": processed_contracts / total_contracts if total_contracts > 0 else 0,
            "errors": errors,
            "processing_completed": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Batch processing completed: {processed_contracts}/{total_contracts} contracts processed successfully")
        
        return result
    
    async def search_similar_contracts(
        self,
        query_contract: ContractAnalysis,
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for contracts similar to the given contract.
        
        Args:
            query_contract: The contract to find similar contracts for
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score
            include_metadata: Whether to include detailed metadata
            
        Returns:
            List of similar contract information
        """
        if not self.vector_store:
            await self.initialize()
        
        try:
            # Use contract text as query
            query_text = query_contract.contract_text or ""
            if not query_text.strip():
                logger.warning(f"No contract text for similarity search: {query_contract.id}")
                return []
            
            # Prepare search query
            from ..services.vector_store_service import SimilaritySearchQuery
            
            search_query = SimilaritySearchQuery(
                query_text=query_text,
                similarity_threshold=similarity_threshold,
                max_results=max_results,
                include_scores=True
            )
            
            # Perform search
            search_results = await self.vector_store.search_similar_contracts(search_query)
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    "contract_id": result.contract_id,
                    "similarity_score": result.similarity_score,
                    "chunk_text": result.chunk_text,
                    "filename": result.metadata.filename,
                    "contract_type": result.metadata.contract_type,
                    "risk_level": result.metadata.risk_level,
                    "jurisdiction": result.metadata.jurisdiction
                }
                
                if include_metadata:
                    formatted_result["metadata"] = result.metadata.dict()
                
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} similar contracts for {query_contract.id}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar contracts for {query_contract.id}: {e}")
            return []
    
    async def update_contract_embeddings(
        self,
        contract_analysis: ContractAnalysis,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Update embeddings for a job application tracking.
        
        Args:
            contract_analysis: The job application tracking to update
            force_regenerate: Whether to force regeneration of embeddings
            
        Returns:
            Dict containing update results
        """
        if not self.vector_store:
            await self.initialize()
        
        try:
            contract_id = str(contract_analysis.id)
            
            # Check if embeddings already exist
            existing_embeddings = []
            if not force_regenerate:
                # This would check the database for existing embeddings
                # For now, we'll assume we need to regenerate
                pass
            
            # Delete existing embeddings if force regenerate
            if force_regenerate or existing_embeddings:
                await self.vector_store.delete_contract_embeddings(contract_id)
                logger.info(f"Deleted existing embeddings for contract {contract_id}")
            
            # Generate new embeddings
            result = await self.process_contract_analysis(contract_analysis)
            
            if result.get("success"):
                logger.info(f"Successfully updated embeddings for contract {contract_id}")
            else:
                logger.error(f"Failed to update embeddings for contract {contract_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update contract embeddings for {contract_analysis.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "contract_analysis_id": str(contract_analysis.id)
            }
    
    async def cleanup_orphaned_embeddings(self) -> Dict[str, Any]:
        """
        Clean up embeddings that no longer have associated contract analyses.
        
        Returns:
            Dict containing cleanup results
        """
        if not self.vector_store:
            await self.initialize()
        
        try:
            logger.info("Starting cleanup of orphaned embeddings")
            
            # This would involve:
            # 1. Getting all embedding IDs from ChromaDB
            # 2. Checking which contract analyses still exist in the database
            # 3. Deleting embeddings for non-existent contracts
            
            # For now, return a placeholder result
            result = {
                "success": True,
                "orphaned_embeddings_found": 0,
                "orphaned_embeddings_deleted": 0,
                "cleanup_completed": datetime.utcnow().isoformat()
            }
            
            logger.info("Orphaned embeddings cleanup completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned embeddings: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_contract_metadata(self, contract_analysis: ContractAnalysis) -> Dict[str, Any]:
        """Prepare metadata for contract embeddings."""
        # Extract risk information
        risky_clauses = contract_analysis.risky_clauses or {}
        risk_score = contract_analysis.risk_score or 0.0
        
        # Determine risk level
        risk_level = "Low"
        if risk_score >= 0.8:
            risk_level = "Critical"
        elif risk_score >= 0.6:
            risk_level = "High"
        elif risk_score >= 0.4:
            risk_level = "Medium"
        
        # Extract contract type (simplified logic)
        filename = contract_analysis.filename.lower()
        contract_type = "unknown"
        if "service" in filename or "agreement" in filename:
            contract_type = "service_agreement"
        elif "employment" in filename:
            contract_type = "employment"
        elif "nda" in filename or "confidentiality" in filename:
            contract_type = "nda"
        elif "license" in filename:
            contract_type = "license"
        
        return {
            "filename": contract_analysis.filename,
            "file_hash": contract_analysis.file_hash,
            "contract_type": contract_type,
            "risk_level": risk_level,
            "risk_score": float(risk_score),
            "analysis_status": contract_analysis.analysis_status,
            "ai_model_used": contract_analysis.ai_model_used,
            "created_at": contract_analysis.created_at.isoformat() if contract_analysis.created_at else None,
            "file_size": contract_analysis.file_size
        }
    
    async def _store_embedding_metadata(
        self,
        contract_analysis: ContractAnalysis,
        embeddings: List[Any]
    ) -> List[Any]:
        """Store embedding metadata in the database."""
        try:
            # This would use the ContractEmbeddingRepository to store metadata
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Failed to store embedding metadata: {e}")
            return []


# Global instance
_integration_service: Optional[ContractEmbeddingIntegrationService] = None


async def get_contract_embedding_integration_service() -> ContractEmbeddingIntegrationService:
    """Get the global contract embedding integration service instance."""
    global _integration_service
    if _integration_service is None:
        _integration_service = ContractEmbeddingIntegrationService()
        await _integration_service.initialize()
    return _integration_service