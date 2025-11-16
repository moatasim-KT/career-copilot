"""
Vector Store Backend Abstraction Layer

This module provides a provider-agnostic interface for vector database operations,
enabling easy switching between ChromaDB, Pinecone, Weaviate, Qdrant, and other providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VectorStoreConfig:
	"""Configuration for vector store backend."""

	backend_type: str  # "chromadb", "pinecone", "weaviate", "qdrant"
	connection_params: Dict[str, Any]
	embedding_dimension: int = 1536
	distance_metric: str = "cosine"  # "cosine", "euclidean", "dot_product"

	# Performance settings
	batch_size: int = 100
	connection_pool_size: int = 10
	timeout: int = 30

	# Caching
	enable_cache: bool = True
	cache_ttl: int = 3600


@dataclass
class EmbeddingBatch:
	"""Batch of embeddings for storage."""

	ids: List[str]
	embeddings: List[List[float]]
	documents: List[str]
	metadata: List[Dict[str, Any]]


@dataclass
class SearchResult:
	"""Single search result from vector store."""

	id: str
	score: float
	document: str
	metadata: Dict[str, Any]
	embedding: Optional[List[float]] = None


@dataclass
class SearchQuery:
	"""Vector similarity search query."""

	query_embedding: List[float]
	limit: int = 10
	filters: Optional[Dict[str, Any]] = None
	include_embeddings: bool = False
	include_metadata: bool = True
	score_threshold: Optional[float] = None


class VectorStoreBackend(ABC):
	"""Abstract base class for vector store backends.

	This interface defines the contract that all vector store implementations
	must follow, enabling seamless switching between providers.
	"""

	def __init__(self, config: VectorStoreConfig):
		"""Initialize the backend with configuration.

		Args:
			config: Backend configuration
		"""
		self.config = config
		self.logger = logger

	@abstractmethod
	async def initialize(self) -> None:
		"""Initialize the backend connection and resources.

		This method should establish connections, create connection pools,
		and perform any necessary setup.

		Raises:
			ConnectionError: If connection cannot be established
		"""
		pass

	@abstractmethod
	async def close(self) -> None:
		"""Close connections and cleanup resources.

		This method should gracefully shutdown connections and release resources.
		"""
		pass

	@abstractmethod
	async def create_collection(
		self, name: str, dimension: Optional[int] = None, distance_metric: Optional[str] = None, metadata_config: Optional[Dict[str, Any]] = None
	) -> None:
		"""Create a new collection/index.

		Args:
			name: Collection name
			dimension: Embedding dimension (defaults to config.embedding_dimension)
			distance_metric: Distance metric (defaults to config.distance_metric)
			metadata_config: Backend-specific metadata configuration

		Raises:
			CollectionExistsError: If collection already exists
		"""
		pass

	@abstractmethod
	async def delete_collection(self, name: str) -> None:
		"""Delete a collection/index.

		Args:
			name: Collection name to delete

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def list_collections(self) -> List[str]:
		"""List all available collections.

		Returns:
			List of collection names
		"""
		pass

	@abstractmethod
	async def collection_exists(self, name: str) -> bool:
		"""Check if a collection exists.

		Args:
			name: Collection name

		Returns:
			True if collection exists, False otherwise
		"""
		pass

	@abstractmethod
	async def add_embeddings(self, collection: str, batch: EmbeddingBatch) -> None:
		"""Add embeddings to a collection.

		Args:
			collection: Collection name
			batch: Batch of embeddings to add

		Raises:
			CollectionNotFoundError: If collection doesn't exist
			ValidationError: If batch data is invalid
		"""
		pass

	@abstractmethod
	async def update_embeddings(self, collection: str, batch: EmbeddingBatch) -> None:
		"""Update existing embeddings in a collection.

		Args:
			collection: Collection name
			batch: Batch of embeddings to update

		Raises:
			CollectionNotFoundError: If collection doesn't exist
			EmbeddingNotFoundError: If any embedding ID doesn't exist
		"""
		pass

	@abstractmethod
	async def delete_embeddings(self, collection: str, ids: List[str]) -> int:
		"""Delete embeddings by IDs.

		Args:
			collection: Collection name
			ids: List of embedding IDs to delete

		Returns:
			Number of embeddings deleted

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def get_embeddings(
		self, collection: str, ids: List[str], include_embeddings: bool = True, include_metadata: bool = True
	) -> List[Dict[str, Any]]:
		"""Retrieve embeddings by IDs.

		Args:
			collection: Collection name
			ids: List of embedding IDs to retrieve
			include_embeddings: Whether to include embedding vectors
			include_metadata: Whether to include metadata

		Returns:
			List of embedding data dicts

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def search(self, collection: str, query: SearchQuery) -> List[SearchResult]:
		"""Perform similarity search.

		Args:
			collection: Collection name
			query: Search query with embedding and parameters

		Returns:
			List of search results ordered by similarity score

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def batch_search(self, collection: str, queries: List[SearchQuery]) -> List[List[SearchResult]]:
		"""Perform multiple similarity searches in batch.

		Args:
			collection: Collection name
			queries: List of search queries

		Returns:
			List of result lists, one per query

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def count(self, collection: str) -> int:
		"""Get total count of embeddings in collection.

		Args:
			collection: Collection name

		Returns:
			Total number of embeddings

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def get_stats(self, collection: str) -> Dict[str, Any]:
		"""Get statistics about a collection.

		Args:
			collection: Collection name

		Returns:
			Dict with statistics (count, dimension, etc.)

		Raises:
			CollectionNotFoundError: If collection doesn't exist
		"""
		pass

	@abstractmethod
	async def health_check(self) -> Dict[str, Any]:
		"""Perform health check on the backend.

		Returns:
			Dict with health status and metrics
		"""
		pass

	# Optional methods with default implementations

	async def optimize_collection(self, collection: str) -> None:
		"""Optimize collection for better performance (if supported).

		Args:
			collection: Collection name
		"""
		logger.info(f"Collection optimization not implemented for {self.config.backend_type}")

	async def create_index(self, collection: str, field: str, index_type: str = "hnsw") -> None:
		"""Create an index on a metadata field (if supported).

		Args:
			collection: Collection name
			field: Metadata field to index
			index_type: Type of index ("hnsw", "flat", etc.)
		"""
		logger.info(f"Metadata indexing not implemented for {self.config.backend_type}")

	async def backup_collection(self, collection: str, backup_path: str) -> None:
		"""Create a backup of a collection (if supported).

		Args:
			collection: Collection name
			backup_path: Path to store backup
		"""
		logger.info(f"Backup not implemented for {self.config.backend_type}")

	async def restore_collection(self, collection: str, backup_path: str) -> None:
		"""Restore a collection from backup (if supported).

		Args:
			collection: Collection name
			backup_path: Path to backup file
		"""
		logger.info(f"Restore not implemented for {self.config.backend_type}")


class VectorStoreFactory:
	"""Factory for creating vector store backend instances."""

	_backends: ClassVar[Dict[str, type]] = {}

	@classmethod
	def register_backend(cls, backend_type: str, backend_class: type) -> None:
		"""Register a vector store backend implementation.

		Args:
			backend_type: Backend identifier (e.g., "chromadb", "pinecone")
			backend_class: Backend class implementing VectorStoreBackend
		"""
		cls._backends[backend_type] = backend_class
		logger.info(f"Registered vector store backend: {backend_type}")

	@classmethod
	def create_backend(cls, config: VectorStoreConfig) -> VectorStoreBackend:
		"""Create a backend instance from configuration.

		Args:
			config: Backend configuration

		Returns:
			Initialized backend instance

		Raises:
			ValueError: If backend_type is not registered
		"""
		backend_class = cls._backends.get(config.backend_type)
		if not backend_class:
			raise ValueError(f"Unknown backend type: {config.backend_type}. Available backends: {list(cls._backends.keys())}")

		return backend_class(config)

	@classmethod
	def list_backends(cls) -> List[str]:
		"""Get list of registered backend types.

		Returns:
			List of backend type strings
		"""
		return list(cls._backends.keys())
