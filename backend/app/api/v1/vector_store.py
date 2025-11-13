"""
Vector Store API endpoints for contract embeddings and similarity search.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

"""
Vector Store API endpoints for contract embeddings and similarity search.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.database_models import User
from ...services.vector_store_service import (
	BatchEmbeddingRequest,
	BatchEmbeddingResult,
	ContractEmbedding,
	EmbeddingStats,
	SimilaritySearchQuery,
	SimilaritySearchResult,
	VectorStoreService,
	get_vector_store_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/vector-store", tags=["vector-store"])


class StoreEmbeddingsRequest(BaseModel):
	"""Request to store contract embeddings."""

	contract_id: str = Field(..., description="Unique contract identifier")
	contract_text: str = Field(..., description="Contract text content")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Contract metadata")
	chunk_size: Optional[int] = Field(default=1000, ge=100, le=5000, description="Text chunk size")
	overlap: Optional[int] = Field(default=200, ge=0, le=1000, description="Chunk overlap size")


class StoreEmbeddingsResponse(BaseModel):
	"""Response from storing contract embeddings."""

	contract_id: str
	embeddings_count: int
	processing_time_ms: float
	embeddings: List[ContractEmbedding]


class SearchContractsRequest(BaseModel):
	"""Request to search similar contracts."""

	query_text: str = Field(..., description="Search query text")
	similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
	max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
	metadata_filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")
	contract_types: Optional[List[str]] = Field(default=None, description="Filter by contract types")
	risk_levels: Optional[List[str]] = Field(default=None, description="Filter by risk levels")
	jurisdictions: Optional[List[str]] = Field(default=None, description="Filter by jurisdictions")


class SearchContractsResponse(BaseModel):
	"""Response from contract similarity search."""

	query_text: str
	results_count: int
	search_time_ms: float
	results: List[SimilaritySearchResult]


class SearchPrecedentsRequest(BaseModel):
	"""Request to search legal precedents."""

	query_text: str = Field(..., description="Legal query text")
	max_results: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
	similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
	jurisdiction: Optional[str] = Field(default=None, description="Filter by jurisdiction")


class SearchPrecedentsResponse(BaseModel):
	"""Response from legal precedent search."""

	query_text: str
	jurisdiction: Optional[str]
	results_count: int
	results: List[SimilaritySearchResult]


class HealthCheckResponse(BaseModel):
	"""Vector store health check response."""

	status: str
	collections: Dict[str, int]
	total_embeddings: int
	total_contracts: int
	search_response_time_ms: float
	timestamp: str


@router.post("/embeddings", response_model=StoreEmbeddingsResponse)
async def store_contract_embeddings(
	request: StoreEmbeddingsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Store embeddings for a contract.

	This endpoint generates and stores vector embeddings for the provided contract text.
	The text is automatically chunked for optimal embedding generation.
	"""
	try:
		start_time = datetime.now(timezone.utc)

		# Store embeddings
		embeddings = await vector_service.store_contract_embeddings(
			contract_id=request.contract_id,
			contract_text=request.contract_text,
			metadata=request.metadata,
			chunk_size=request.chunk_size,
			overlap=request.overlap,
		)

		processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

		logger.info(f"Stored {len(embeddings)} embeddings for contract {request.contract_id}")

		return StoreEmbeddingsResponse(
			contract_id=request.contract_id, embeddings_count=len(embeddings), processing_time_ms=processing_time, embeddings=embeddings
		)

	except Exception as e:
		logger.error(f"Failed to store embeddings for contract {request.contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to store contract embeddings: {e!s}")


@router.post("/search/contracts", response_model=SearchContractsResponse)
async def search_similar_contracts(
	request: SearchContractsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Search for similar contracts using vector similarity.

	This endpoint performs semantic similarity search across stored contract embeddings
	to find contracts with similar content, clauses, or legal concepts.
	"""
	try:
		start_time = datetime.now(timezone.utc)

		# Create search query
		query = SimilaritySearchQuery(
			query_text=request.query_text,
			similarity_threshold=request.similarity_threshold,
			max_results=request.max_results,
			metadata_filters=request.metadata_filters,
			contract_types=request.contract_types,
			risk_levels=request.risk_levels,
			jurisdictions=request.jurisdictions,
		)

		# Perform search
		results = await vector_service.search_similar_contracts(query)

		search_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

		logger.info(f"Found {len(results)} similar contracts for query: {request.query_text[:50]}...")

		return SearchContractsResponse(query_text=request.query_text, results_count=len(results), search_time_ms=search_time, results=results)

	except Exception as e:
		logger.error(f"Failed to search similar contracts: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search similar contracts: {e!s}")


@router.post("/search/precedents", response_model=SearchPrecedentsResponse)
async def search_legal_precedents(
	request: SearchPrecedentsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Search for legal precedents related to the query.

	This endpoint searches through legal precedent embeddings to find relevant
	case law, regulations, and legal principles related to the query text.
	"""
	try:
		# Perform precedent search
		results = await vector_service.search_legal_precedents(
			query_text=request.query_text,
			max_results=request.max_results,
			similarity_threshold=request.similarity_threshold,
			jurisdiction=request.jurisdiction,
		)

		logger.info(f"Found {len(results)} legal precedents for query: {request.query_text[:50]}...")

		return SearchPrecedentsResponse(query_text=request.query_text, jurisdiction=request.jurisdiction, results_count=len(results), results=results)

	except Exception as e:
		logger.error(f"Failed to search legal precedents: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search legal precedents: {e!s}")


@router.post("/batch/embeddings", response_model=BatchEmbeddingResult)
async def batch_store_embeddings(
	request: BatchEmbeddingRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Store embeddings for multiple contracts in batches.

	This endpoint processes multiple contracts concurrently for improved performance
	when dealing with large volumes of contracts.
	"""
	try:
		logger.info(f"Starting batch embedding for {len(request.contracts)} contracts")

		# Process batch embeddings
		result = await vector_service.batch_store_embeddings(request)

		logger.info(f"Batch embedding completed: {result.processed_contracts}/{result.total_contracts} contracts processed")

		return result

	except Exception as e:
		logger.error(f"Failed to process batch embeddings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process batch embeddings: {e!s}")


@router.delete("/embeddings/{contract_id}")
async def delete_contract_embeddings(
	contract_id: str, current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""
	Delete all embeddings for a specific contract.

	This endpoint removes all stored embeddings associated with the given contract ID.
	"""
	try:
		success = await vector_service.delete_contract_embeddings(contract_id)

		if success:
			logger.info(f"Deleted embeddings for contract {contract_id}")
			return {"message": f"Successfully deleted embeddings for contract {contract_id}"}
		else:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No embeddings found for contract {contract_id}")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to delete embeddings for contract {contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete contract embeddings: {e!s}")


@router.get("/stats", response_model=EmbeddingStats)
async def get_embedding_statistics(
	current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""
	Get statistics about stored embeddings.

	This endpoint provides comprehensive statistics about the vector store,
	including counts, performance metrics, and storage information.
	"""
	try:
		stats = await vector_service.get_embedding_stats()

		logger.debug(f"Retrieved embedding statistics: {stats.total_embeddings} embeddings, {stats.total_contracts} contracts")

		return stats

	except Exception as e:
		logger.error(f"Failed to get embedding statistics: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get embedding statistics: {e!s}")


@router.get("/health", response_model=HealthCheckResponse)
async def vector_store_health_check(vector_service: VectorStoreService = Depends(get_vector_store_service)):
	"""
	Perform health check on the vector store service.

	This endpoint checks the health and performance of the vector store,
	including connectivity, response times, and basic functionality.
	"""
	try:
		health_info = await vector_service.health_check()

		if health_info["status"] == "healthy":
			return HealthCheckResponse(**health_info)
		else:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Vector store is unhealthy: {health_info.get('error', 'Unknown error')}"
			)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Vector store health check failed: {e}")
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Vector store health check failed: {e!s}")


# Additional utility endpoints


@router.get("/collections")
async def list_collections(current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)):
	"""List all available collections in the vector store."""
	try:
		collections = list(vector_service.collections.keys())

		return {"collections": collections, "count": len(collections), "timestamp": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Failed to list collections: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list collections: {e!s}")


@router.get("/contracts/{contract_id}/embeddings")
async def get_contract_embeddings(
	contract_id: str, current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""Get all embeddings for a specific contract."""
	try:
		if not vector_service.chroma_client:
			await vector_service.initialize()

		collection = vector_service.collections[vector_service.contracts_collection]

		# Get embeddings for this contract
		results = collection.get(where={"contract_id": contract_id}, include=["documents", "metadatas"])

		if not results["ids"]:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No embeddings found for contract {contract_id}")

		embeddings = []
		for i, (doc_id, document, metadata) in enumerate(zip(results["ids"], results["documents"], results["metadatas"])):
			embeddings.append({"id": doc_id, "chunk_index": metadata.get("chunk_index", i), "chunk_text": document, "metadata": metadata})

		return {
			"contract_id": contract_id,
			"embeddings_count": len(embeddings),
			"embeddings": embeddings,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get embeddings for contract {contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get contract embeddings: {e!s}")

from ...core.logging import get_logger
from ...models.database_models import User
from ...services.vector_store_service import (
	BatchEmbeddingRequest,
	BatchEmbeddingResult,
	ContractEmbedding,
	EmbeddingStats,
	SimilaritySearchQuery,
	SimilaritySearchResult,
	VectorStoreService,
	get_vector_store_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/vector-store", tags=["vector-store"])


class StoreEmbeddingsRequest(BaseModel):
	"""Request to store contract embeddings."""

	contract_id: str = Field(..., description="Unique contract identifier")
	contract_text: str = Field(..., description="Contract text content")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Contract metadata")
	chunk_size: Optional[int] = Field(default=1000, ge=100, le=5000, description="Text chunk size")
	overlap: Optional[int] = Field(default=200, ge=0, le=1000, description="Chunk overlap size")


class StoreEmbeddingsResponse(BaseModel):
	"""Response from storing contract embeddings."""

	contract_id: str
	embeddings_count: int
	processing_time_ms: float
	embeddings: List[ContractEmbedding]


class SearchContractsRequest(BaseModel):
	"""Request to search similar contracts."""

	query_text: str = Field(..., description="Search query text")
	similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
	max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
	metadata_filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")
	contract_types: Optional[List[str]] = Field(default=None, description="Filter by contract types")
	risk_levels: Optional[List[str]] = Field(default=None, description="Filter by risk levels")
	jurisdictions: Optional[List[str]] = Field(default=None, description="Filter by jurisdictions")


class SearchContractsResponse(BaseModel):
	"""Response from contract similarity search."""

	query_text: str
	results_count: int
	search_time_ms: float
	results: List[SimilaritySearchResult]


class SearchPrecedentsRequest(BaseModel):
	"""Request to search legal precedents."""

	query_text: str = Field(..., description="Legal query text")
	max_results: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
	similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
	jurisdiction: Optional[str] = Field(default=None, description="Filter by jurisdiction")


class SearchPrecedentsResponse(BaseModel):
	"""Response from legal precedent search."""

	query_text: str
	jurisdiction: Optional[str]
	results_count: int
	results: List[SimilaritySearchResult]


class HealthCheckResponse(BaseModel):
	"""Vector store health check response."""

	status: str
	collections: Dict[str, int]
	total_embeddings: int
	total_contracts: int
	search_response_time_ms: float
	timestamp: str


@router.post("/embeddings", response_model=StoreEmbeddingsResponse)
async def store_contract_embeddings(
	request: StoreEmbeddingsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Store embeddings for a contract.

	This endpoint generates and stores vector embeddings for the provided contract text.
	The text is automatically chunked for optimal embedding generation.
	"""
	try:
		start_time = datetime.now(timezone.utc)

		# Store embeddings
		embeddings = await vector_service.store_contract_embeddings(
			contract_id=request.contract_id,
			contract_text=request.contract_text,
			metadata=request.metadata,
			chunk_size=request.chunk_size,
			overlap=request.overlap,
		)

		processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

		logger.info(f"Stored {len(embeddings)} embeddings for contract {request.contract_id}")

		return StoreEmbeddingsResponse(
			contract_id=request.contract_id, embeddings_count=len(embeddings), processing_time_ms=processing_time, embeddings=embeddings
		)

	except Exception as e:
		logger.error(f"Failed to store embeddings for contract {request.contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to store contract embeddings: {e!s}")


@router.post("/search/contracts", response_model=SearchContractsResponse)
async def search_similar_contracts(
	request: SearchContractsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Search for similar contracts using vector similarity.

	This endpoint performs semantic similarity search across stored contract embeddings
	to find contracts with similar content, clauses, or legal concepts.
	"""
	try:
		start_time = datetime.now(timezone.utc)

		# Create search query
		query = SimilaritySearchQuery(
			query_text=request.query_text,
			similarity_threshold=request.similarity_threshold,
			max_results=request.max_results,
			metadata_filters=request.metadata_filters,
			contract_types=request.contract_types,
			risk_levels=request.risk_levels,
			jurisdictions=request.jurisdictions,
		)

		# Perform search
		results = await vector_service.search_similar_contracts(query)

		search_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

		logger.info(f"Found {len(results)} similar contracts for query: {request.query_text[:50]}...")

		return SearchContractsResponse(query_text=request.query_text, results_count=len(results), search_time_ms=search_time, results=results)

	except Exception as e:
		logger.error(f"Failed to search similar contracts: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search similar contracts: {e!s}")


@router.post("/search/precedents", response_model=SearchPrecedentsResponse)
async def search_legal_precedents(
	request: SearchPrecedentsRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Search for legal precedents related to the query.

	This endpoint searches through legal precedent embeddings to find relevant
	case law, regulations, and legal principles related to the query text.
	"""
	try:
		# Perform precedent search
		results = await vector_service.search_legal_precedents(
			query_text=request.query_text,
			max_results=request.max_results,
			similarity_threshold=request.similarity_threshold,
			jurisdiction=request.jurisdiction,
		)

		logger.info(f"Found {len(results)} legal precedents for query: {request.query_text[:50]}...")

		return SearchPrecedentsResponse(query_text=request.query_text, jurisdiction=request.jurisdiction, results_count=len(results), results=results)

	except Exception as e:
		logger.error(f"Failed to search legal precedents: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search legal precedents: {e!s}")


@router.post("/batch/embeddings", response_model=BatchEmbeddingResult)
async def batch_store_embeddings(
	request: BatchEmbeddingRequest,
	current_user: User = Depends(get_current_user),
	vector_service: VectorStoreService = Depends(get_vector_store_service),
):
	"""
	Store embeddings for multiple contracts in batches.

	This endpoint processes multiple contracts concurrently for improved performance
	when dealing with large volumes of contracts.
	"""
	try:
		logger.info(f"Starting batch embedding for {len(request.contracts)} contracts")

		# Process batch embeddings
		result = await vector_service.batch_store_embeddings(request)

		logger.info(f"Batch embedding completed: {result.processed_contracts}/{result.total_contracts} contracts processed")

		return result

	except Exception as e:
		logger.error(f"Failed to process batch embeddings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process batch embeddings: {e!s}")


@router.delete("/embeddings/{contract_id}")
async def delete_contract_embeddings(
	contract_id: str, current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""
	Delete all embeddings for a specific contract.

	This endpoint removes all stored embeddings associated with the given contract ID.
	"""
	try:
		success = await vector_service.delete_contract_embeddings(contract_id)

		if success:
			logger.info(f"Deleted embeddings for contract {contract_id}")
			return {"message": f"Successfully deleted embeddings for contract {contract_id}"}
		else:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No embeddings found for contract {contract_id}")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to delete embeddings for contract {contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete contract embeddings: {e!s}")


@router.get("/stats", response_model=EmbeddingStats)
async def get_embedding_statistics(
	current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""
	Get statistics about stored embeddings.

	This endpoint provides comprehensive statistics about the vector store,
	including counts, performance metrics, and storage information.
	"""
	try:
		stats = await vector_service.get_embedding_stats()

		logger.debug(f"Retrieved embedding statistics: {stats.total_embeddings} embeddings, {stats.total_contracts} contracts")

		return stats

	except Exception as e:
		logger.error(f"Failed to get embedding statistics: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get embedding statistics: {e!s}")


@router.get("/health", response_model=HealthCheckResponse)
async def vector_store_health_check(vector_service: VectorStoreService = Depends(get_vector_store_service)):
	"""
	Perform health check on the vector store service.

	This endpoint checks the health and performance of the vector store,
	including connectivity, response times, and basic functionality.
	"""
	try:
		health_info = await vector_service.health_check()

		if health_info["status"] == "healthy":
			return HealthCheckResponse(**health_info)
		else:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Vector store is unhealthy: {health_info.get('error', 'Unknown error')}"
			)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Vector store health check failed: {e}")
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Vector store health check failed: {e!s}")


# Additional utility endpoints


@router.get("/collections")
async def list_collections(current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)):
	"""List all available collections in the vector store."""
	try:
		collections = list(vector_service.collections.keys())

		return {"collections": collections, "count": len(collections), "timestamp": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Failed to list collections: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list collections: {e!s}")


@router.get("/contracts/{contract_id}/embeddings")
async def get_contract_embeddings(
	contract_id: str, current_user: User = Depends(get_current_user), vector_service: VectorStoreService = Depends(get_vector_store_service)
):
	"""Get all embeddings for a specific contract."""
	try:
		if not vector_service.chroma_client:
			await vector_service.initialize()

		collection = vector_service.collections[vector_service.contracts_collection]

		# Get embeddings for this contract
		results = collection.get(where={"contract_id": contract_id}, include=["documents", "metadatas"])

		if not results["ids"]:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No embeddings found for contract {contract_id}")

		embeddings = []
		for i, (doc_id, document, metadata) in enumerate(zip(results["ids"], results["documents"], results["metadatas"])):
			embeddings.append({"id": doc_id, "chunk_index": metadata.get("chunk_index", i), "chunk_text": document, "metadata": metadata})

		return {
			"contract_id": contract_id,
			"embeddings_count": len(embeddings),
			"embeddings": embeddings,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get embeddings for contract {contract_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get contract embeddings: {e!s}")
