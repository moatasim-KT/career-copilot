"""
Vector Store Service for Contract Embeddings and Similarity Search.

This service provides comprehensive functionality for:
- Contract embedding generation and storage
- Similarity search for legal precedents
- Metadata filtering for search results
- Batch embedding operations for performance
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import numpy as np
from chromadb.api.models.Collection import Collection
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import VectorStoreError
from ..core.logging import get_logger
from .chroma_client import get_chroma_client

logger = get_logger(__name__)


class PrecedentClause(BaseModel):
    """Legal precedent clause model for compatibility with legal precedent agent."""
    id: str
    text: str
    category: str
    risk_level: str
    effectiveness_score: float
    source_document: str
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class EmbeddingMetadata(BaseModel):
    """Metadata for contract embeddings."""
    contract_id: str
    filename: str
    file_hash: str
    chunk_index: int
    chunk_size: int
    total_chunks: int
    contract_type: Optional[str] = None
    risk_level: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Legal context metadata
    jurisdiction: Optional[str] = None
    contract_category: Optional[str] = None
    parties: Optional[List[str]] = None
    key_terms: Optional[List[str]] = None
    
    # Processing metadata
    embedding_model: str = "text-embedding-ada-002"
    processing_time_ms: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ContractEmbedding(BaseModel):
    """Contract embedding with metadata."""
    id: str
    contract_id: str
    chunk_text: str
    embedding: List[float]
    metadata: EmbeddingMetadata
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SimilaritySearchQuery(BaseModel):
    """Query for similarity search."""
    query_text: str
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_results: int = Field(default=10, ge=1, le=100)
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    include_scores: bool = True
    contract_types: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None
    jurisdictions: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None


class SimilaritySearchResult(BaseModel):
    """Result from similarity search."""
    id: str
    contract_id: str
    chunk_text: str
    similarity_score: float
    metadata: EmbeddingMetadata
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BatchEmbeddingRequest(BaseModel):
    """Request for batch embedding operations."""
    contracts: List[Dict[str, Any]]
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    overlap_size: int = Field(default=200, ge=0, le=1000)
    batch_size: int = Field(default=10, ge=1, le=50)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BatchEmbeddingResult(BaseModel):
    """Result from batch embedding operations."""
    total_contracts: int
    processed_contracts: int
    failed_contracts: int
    total_embeddings: int
    processing_time_seconds: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


@dataclass
class EmbeddingStats:
    """Statistics for embedding operations."""
    total_embeddings: int = 0
    total_contracts: int = 0
    average_chunks_per_contract: float = 0.0
    total_storage_size_mb: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Performance metrics
    average_embedding_time_ms: float = 0.0
    average_search_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Collection statistics
    collections: Dict[str, int] = field(default_factory=dict)


class VectorStoreService:
    """Service for managing contract embeddings and similarity search."""
    
    def __init__(self):
        self.settings = get_settings()
        self.chroma_client = None
        self.collections: Dict[str, Collection] = {}
        
        # Collection names
        self.contracts_collection = "contract_embeddings"
        self.precedents_collection = "legal_precedents"
        
        # Chunking parameters
        self.default_chunk_size = 1000
        self.default_overlap = 200
        
        # Performance tracking
        self._embedding_times: List[float] = []
        self._search_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
    
    async def initialize(self):
        """Initialize the vector store service."""
        if self.chroma_client is not None:
            return
        
        self.chroma_client = await get_chroma_client()
        
        # Initialize collections
        await self._initialize_collections()
        
        logger.info("Vector store service initialized")
    
    async def _initialize_collections(self):
        """Initialize ChromaDB collections."""
        try:
            # Contract embeddings collection
            self.collections[self.contracts_collection] = await self.chroma_client.get_or_create_collection(
                name=self.contracts_collection,
                metadata={
                    "description": "Contract text embeddings for similarity search",
                    "embedding_model": "text-embedding-ada-002",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Legal precedents collection
            self.collections[self.precedents_collection] = await self.chroma_client.get_or_create_collection(
                name=self.precedents_collection,
                metadata={
                    "description": "Legal precedent embeddings for case law search",
                    "embedding_model": "text-embedding-ada-002",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Initialized collections: {list(self.collections.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise VectorStoreError(f"Failed to initialize collections: {e}")
    
    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks."""
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_end = text.rfind('.', end - 100, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_embedding_id(self, contract_id: str, chunk_index: int) -> str:
        """Generate unique ID for embedding."""
        content = f"{contract_id}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _prepare_chroma_metadata(self, metadata: EmbeddingMetadata) -> Dict[str, Any]:
        """Convert EmbeddingMetadata to ChromaDB-compatible format."""
        chroma_metadata = {}
        
        # Convert all fields to ChromaDB-compatible types
        for key, value in metadata.dict().items():
            if value is None:
                chroma_metadata[key] = None
            elif isinstance(value, datetime):
                chroma_metadata[key] = value.isoformat()
            elif isinstance(value, list):
                # Convert lists to comma-separated strings for ChromaDB
                chroma_metadata[key] = ",".join(str(item) for item in value) if value else ""
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                chroma_metadata[key] = json.dumps(value) if value else "{}"
            elif isinstance(value, (str, int, float, bool)):
                chroma_metadata[key] = value
            else:
                # Convert other types to string
                chroma_metadata[key] = str(value)
        
        return chroma_metadata
    
    def _reconstruct_metadata(self, chroma_metadata: Dict[str, Any]) -> EmbeddingMetadata:
        """Reconstruct EmbeddingMetadata from ChromaDB format."""
        try:
            # Convert ChromaDB metadata back to proper types
            reconstructed = {}
            
            for key, value in chroma_metadata.items():
                if key in ["created_at", "updated_at"] and isinstance(value, str):
                    try:
                        reconstructed[key] = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        reconstructed[key] = datetime.utcnow()
                elif key in ["parties", "key_terms"] and isinstance(value, str):
                    # Convert comma-separated strings back to lists
                    reconstructed[key] = [item.strip() for item in value.split(",") if item.strip()] if value else []
                elif key == "additional_metadata" and isinstance(value, str):
                    # Convert JSON strings back to dicts
                    try:
                        reconstructed[key] = json.loads(value) if value else {}
                    except (json.JSONDecodeError, TypeError):
                        reconstructed[key] = {}
                else:
                    reconstructed[key] = value
            
            # Ensure required fields have default values
            if "created_at" not in reconstructed:
                reconstructed["created_at"] = datetime.utcnow()
            if "updated_at" not in reconstructed:
                reconstructed["updated_at"] = datetime.utcnow()
            
            return EmbeddingMetadata(**reconstructed)
            
        except Exception as e:
            logger.warning(f"Failed to reconstruct metadata: {e}")
            # Return minimal metadata if reconstruction fails
            return EmbeddingMetadata(
                contract_id=chroma_metadata.get("contract_id", "unknown"),
                filename=chroma_metadata.get("filename", "unknown"),
                file_hash=chroma_metadata.get("file_hash", ""),
                chunk_index=chroma_metadata.get("chunk_index", 0),
                chunk_size=chroma_metadata.get("chunk_size", 0),
                total_chunks=chroma_metadata.get("total_chunks", 1)
            )
    
    async def store_contract_embeddings(
        self,
        contract_id: str,
        contract_text: str,
        metadata: Dict[str, Any],
        chunk_size: int = None,
        overlap: int = None
    ) -> List[ContractEmbedding]:
        """Store embeddings for a contract."""
        if not self.chroma_client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Chunk the contract text
            chunks = self._chunk_text(contract_text, chunk_size, overlap)
            
            if not chunks:
                raise VectorStoreError("No text chunks generated from contract")
            
            embeddings = []
            collection = self.collections[self.contracts_collection]
            
            # Prepare batch data
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                embedding_id = self._generate_embedding_id(contract_id, i)
                
                # Create embedding metadata
                embedding_metadata = EmbeddingMetadata(
                    contract_id=contract_id,
                    filename=metadata.get("filename", "unknown"),
                    file_hash=metadata.get("file_hash", ""),
                    chunk_index=i,
                    chunk_size=len(chunk),
                    total_chunks=len(chunks),
                    contract_type=metadata.get("contract_type"),
                    risk_level=metadata.get("risk_level"),
                    jurisdiction=metadata.get("jurisdiction"),
                    contract_category=metadata.get("contract_category"),
                    parties=metadata.get("parties", []),
                    key_terms=metadata.get("key_terms", [])
                )
                
                # Convert metadata to ChromaDB-compatible format
                chroma_metadata = self._prepare_chroma_metadata(embedding_metadata)
                
                ids.append(embedding_id)
                documents.append(chunk)
                metadatas.append(chroma_metadata)
                
                # Create embedding object for return
                embeddings.append(ContractEmbedding(
                    id=embedding_id,
                    contract_id=contract_id,
                    chunk_text=chunk,
                    embedding=[],  # Will be populated by ChromaDB
                    metadata=embedding_metadata
                ))
            
            # Store in ChromaDB (embeddings are generated automatically)
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            processing_time = (time.time() - start_time) * 1000
            self._embedding_times.append(processing_time)
            
            # Update metadata with processing time
            for embedding in embeddings:
                embedding.metadata.processing_time_ms = processing_time / len(chunks)
            
            logger.info(f"Stored {len(embeddings)} embeddings for contract {contract_id} in {processing_time:.2f}ms")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to store contract embeddings: {e}")
            raise VectorStoreError(f"Failed to store contract embeddings: {e}")
    
    async def search_similar_contracts(
        self,
        query: SimilaritySearchQuery
    ) -> List[SimilaritySearchResult]:
        """Search for similar contracts using vector similarity."""
        if not self.chroma_client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            collection = self.collections[self.contracts_collection]
            
            # Build metadata filters
            where_clause = {}
            
            # Apply metadata filters
            if query.metadata_filters:
                where_clause.update(query.metadata_filters)
            
            # Apply contract type filters
            if query.contract_types:
                where_clause["contract_type"] = {"$in": query.contract_types}
            
            # Apply risk level filters
            if query.risk_levels:
                where_clause["risk_level"] = {"$in": query.risk_levels}
            
            # Apply jurisdiction filters
            if query.jurisdictions:
                where_clause["jurisdiction"] = {"$in": query.jurisdictions}
            
            # Apply date range filters
            if query.date_range:
                start_date, end_date = query.date_range
                where_clause["created_at"] = {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            
            # Perform similarity search
            results = collection.query(
                query_texts=[query.query_text],
                n_results=query.max_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            search_time = (time.time() - start_time) * 1000
            self._search_times.append(search_time)
            
            # Process results
            similarity_results = []
            
            if results["ids"] and results["ids"][0]:
                for i, (doc_id, document, metadata, distance) in enumerate(zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity_score = 1.0 - distance
                    
                    # Apply similarity threshold
                    if similarity_score >= query.similarity_threshold:
                        # Reconstruct metadata object from ChromaDB format
                        embedding_metadata = self._reconstruct_metadata(metadata)
                        
                        similarity_results.append(SimilaritySearchResult(
                            id=doc_id,
                            contract_id=metadata["contract_id"],
                            chunk_text=document,
                            similarity_score=similarity_score,
                            metadata=embedding_metadata
                        ))
            
            logger.info(f"Found {len(similarity_results)} similar contracts in {search_time:.2f}ms")
            
            return similarity_results
            
        except Exception as e:
            logger.error(f"Failed to search similar contracts: {e}")
            raise VectorStoreError(f"Failed to search similar contracts: {e}")
    
    async def search_legal_precedents(
        self,
        query_text: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        jurisdiction: Optional[str] = None
    ) -> List[SimilaritySearchResult]:
        """Search for legal precedents related to the query."""
        if not self.chroma_client:
            await self.initialize()
        
        try:
            collection = self.collections[self.precedents_collection]
            
            # Build where clause for jurisdiction filter
            where_clause = None
            if jurisdiction:
                where_clause = {"jurisdiction": jurisdiction}
            
            # Perform similarity search
            results = collection.query(
                query_texts=[query_text],
                n_results=max_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            precedent_results = []
            
            if results["ids"] and results["ids"][0]:
                for doc_id, document, metadata, distance in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    similarity_score = 1.0 - distance
                    
                    if similarity_score >= similarity_threshold:
                        embedding_metadata = self._reconstruct_metadata(metadata)
                        
                        precedent_results.append(SimilaritySearchResult(
                            id=doc_id,
                            contract_id=metadata.get("contract_id", ""),
                            chunk_text=document,
                            similarity_score=similarity_score,
                            metadata=embedding_metadata
                        ))
            
            logger.info(f"Found {len(precedent_results)} legal precedents")
            
            return precedent_results
            
        except Exception as e:
            logger.error(f"Failed to search legal precedents: {e}")
            raise VectorStoreError(f"Failed to search legal precedents: {e}")
    
    async def batch_store_embeddings(
        self,
        request: BatchEmbeddingRequest
    ) -> BatchEmbeddingResult:
        """Store embeddings for multiple contracts in batches."""
        if not self.chroma_client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            total_contracts = len(request.contracts)
            processed_contracts = 0
            failed_contracts = 0
            total_embeddings = 0
            errors = []
            
            # Process contracts in batches
            for i in range(0, total_contracts, request.batch_size):
                batch = request.contracts[i:i + request.batch_size]
                
                # Process each contract in the batch
                batch_tasks = []
                for contract_data in batch:
                    task = self._process_single_contract(
                        contract_data,
                        request.chunk_size,
                        request.overlap_size
                    )
                    batch_tasks.append(task)
                
                # Execute batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        failed_contracts += 1
                        errors.append({
                            "contract_index": i + j,
                            "contract_id": batch[j].get("contract_id", "unknown"),
                            "error": str(result)
                        })
                    else:
                        processed_contracts += 1
                        total_embeddings += len(result)
                
                # Log progress
                logger.info(f"Processed batch {i // request.batch_size + 1}/{(total_contracts + request.batch_size - 1) // request.batch_size}")
            
            processing_time = time.time() - start_time
            
            result = BatchEmbeddingResult(
                total_contracts=total_contracts,
                processed_contracts=processed_contracts,
                failed_contracts=failed_contracts,
                total_embeddings=total_embeddings,
                processing_time_seconds=processing_time,
                errors=errors
            )
            
            logger.info(f"Batch embedding completed: {processed_contracts}/{total_contracts} contracts, {total_embeddings} embeddings in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process batch embeddings: {e}")
            raise VectorStoreError(f"Failed to process batch embeddings: {e}")
    
    async def _process_single_contract(
        self,
        contract_data: Dict[str, Any],
        chunk_size: int,
        overlap_size: int
    ) -> List[ContractEmbedding]:
        """Process a single contract for embedding storage."""
        contract_id = contract_data.get("contract_id")
        contract_text = contract_data.get("contract_text", "")
        metadata = contract_data.get("metadata", {})
        
        if not contract_id or not contract_text:
            raise ValueError(f"Invalid contract data: missing contract_id or contract_text")
        
        return await self.store_contract_embeddings(
            contract_id=contract_id,
            contract_text=contract_text,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap_size
        )
    
    async def delete_contract_embeddings(self, contract_id: str) -> bool:
        """Delete all embeddings for a contract."""
        if not self.chroma_client:
            await self.initialize()
        
        try:
            collection = self.collections[self.contracts_collection]
            
            # Find all embeddings for this contract
            results = collection.get(
                where={"contract_id": contract_id},
                include=["metadatas"]
            )
            
            if results["ids"]:
                # Delete the embeddings
                collection.delete(ids=results["ids"])
                
                logger.info(f"Deleted {len(results['ids'])} embeddings for contract {contract_id}")
                return True
            else:
                logger.warning(f"No embeddings found for contract {contract_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete contract embeddings: {e}")
            raise VectorStoreError(f"Failed to delete contract embeddings: {e}")
    
    async def get_embedding_stats(self) -> EmbeddingStats:
        """Get statistics about stored embeddings."""
        if not self.chroma_client:
            await self.initialize()
        
        try:
            stats = EmbeddingStats()
            
            # Get collection statistics
            for collection_name, collection in self.collections.items():
                count = collection.count()
                stats.collections[collection_name] = count
                
                if collection_name == self.contracts_collection:
                    stats.total_embeddings = count
                    
                    # Get unique contracts count
                    if count > 0:
                        results = collection.get(include=["metadatas"])
                        unique_contracts = set()
                        for metadata in results["metadatas"]:
                            unique_contracts.add(metadata["contract_id"])
                        
                        stats.total_contracts = len(unique_contracts)
                        if stats.total_contracts > 0:
                            stats.average_chunks_per_contract = stats.total_embeddings / stats.total_contracts
            
            # Calculate performance metrics
            if self._embedding_times:
                stats.average_embedding_time_ms = sum(self._embedding_times) / len(self._embedding_times)
            
            if self._search_times:
                stats.average_search_time_ms = sum(self._search_times) / len(self._search_times)
            
            # Calculate cache hit rate
            total_requests = self._cache_hits + self._cache_misses
            if total_requests > 0:
                stats.cache_hit_rate = self._cache_hits / total_requests
            
            # Estimate storage size (rough calculation)
            # Assuming 1536 dimensions * 4 bytes per float + metadata overhead
            embedding_size_bytes = stats.total_embeddings * (1536 * 4 + 1000)  # 1KB metadata overhead
            stats.total_storage_size_mb = embedding_size_bytes / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            raise VectorStoreError(f"Failed to get embedding stats: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the vector store service."""
        if not self.chroma_client:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": f"Failed to initialize: {e}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        try:
            # Test basic operations
            stats = await self.get_embedding_stats()
            
            # Test search functionality
            test_query = SimilaritySearchQuery(
                query_text="test query",
                max_results=1
            )
            
            search_start = time.time()
            await self.search_similar_contracts(test_query)
            search_time = (time.time() - search_start) * 1000
            
            return {
                "status": "healthy",
                "collections": stats.collections,
                "total_embeddings": stats.total_embeddings,
                "total_contracts": stats.total_contracts,
                "search_response_time_ms": search_time,
                "average_embedding_time_ms": stats.average_embedding_time_ms,
                "average_search_time_ms": stats.average_search_time_ms,
                "cache_hit_rate": stats.cache_hit_rate,
                "storage_size_mb": stats.total_storage_size_mb,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance
_vector_store_service: Optional[VectorStoreService] = None


async def get_vector_store_service() -> VectorStoreService:
    """Get the global vector store service instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
        await _vector_store_service.initialize()
    return _vector_store_service