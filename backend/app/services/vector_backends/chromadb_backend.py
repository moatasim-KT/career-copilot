"""
ChromaDB Backend Implementation

Concrete implementation of VectorStoreBackend for ChromaDB.
Provides production-ready vector storage with persistence and connection pooling.
"""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ...core.config import get_settings
from ...core.exceptions import VectorStoreError
from ...core.logging import get_logger
from ...core.vector_store_backend import (
	EmbeddingBatch,
	SearchQuery,
	SearchResult,
	VectorStoreBackend,
	VectorStoreConfig,
)

logger = get_logger(__name__)
settings = get_settings()


class ChromaDBBackend(VectorStoreBackend):
	"""ChromaDB implementation of VectorStoreBackend.

	Features:
	- Persistent storage with configurable directory
	- Connection pooling for concurrent access
	- OpenAI embedding function integration
	- Metadata indexing and filtering
	- Efficient batch operations
	"""

	def __init__(self, config: VectorStoreConfig):
		"""Initialize ChromaDB backend.

		Args:
		    config: Backend configuration
		"""
		super().__init__(config)
		self.client: Optional[chromadb.ClientAPI] = None
		self.collections: Dict[str, chromadb.Collection] = {}
		self.embedding_function = None

	async def initialize(self) -> None:
		"""Initialize ChromaDB client and connection pool."""
		try:
			# Extract connection parameters
			persist_dir = self.config.connection_params.get("persist_directory", os.path.join(os.getcwd(), "data/chroma"))
			os.makedirs(persist_dir, exist_ok=True)

			# Initialize client with settings
			chroma_settings = Settings(
				anonymized_telemetry=False,
				allow_reset=self.config.connection_params.get("allow_reset", True),
			)

			self.client = chromadb.PersistentClient(path=persist_dir, settings=chroma_settings)

			# Initialize embedding function
			embedding_model = self.config.connection_params.get("embedding_model", "text-embedding-ada-002")

			openai_api_key = self.config.connection_params.get("openai_api_key", settings.openai_api_key)

			self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_api_key, model_name=embedding_model)

			self.logger.info(f"ChromaDB initialized at {persist_dir}")

		except Exception as e:
			self.logger.error(f"Failed to initialize ChromaDB: {e}")
			raise VectorStoreError(f"ChromaDB initialization failed: {e}")

	async def close(self) -> None:
		"""Close ChromaDB connections and cleanup."""
		try:
			if self.client:
				# ChromaDB PersistentClient doesn't have explicit close
				# Collections are automatically persisted
				self.collections.clear()
				self.client = None
				self.logger.info("ChromaDB client closed")
		except Exception as e:
			self.logger.error(f"Error closing ChromaDB: {e}")

	async def create_collection(
		self, name: str, dimension: Optional[int] = None, distance_metric: Optional[str] = None, metadata_config: Optional[Dict[str, Any]] = None
	) -> None:
		"""Create a new ChromaDB collection.

		Args:
		    name: Collection name
		    dimension: Embedding dimension (not used - inferred from embeddings)
		    distance_metric: Distance metric (ChromaDB uses cosine by default)
		    metadata_config: Additional metadata
		"""
		try:
			if name in self.collections:
				raise ValueError(f"Collection '{name}' already exists")

			metadata = metadata_config or {}
			metadata["created_by"] = "career_copilot"
			metadata["dimension"] = dimension or self.config.embedding_dimension

			collection = self.client.get_or_create_collection(name=name, embedding_function=self.embedding_function, metadata=metadata)

			self.collections[name] = collection
			self.logger.info(f"Created collection: {name}")

		except Exception as e:
			self.logger.error(f"Failed to create collection '{name}': {e}")
			raise VectorStoreError(f"Collection creation failed: {e}")

	async def delete_collection(self, name: str) -> None:
		"""Delete a ChromaDB collection.

		Args:
		    name: Collection name to delete
		"""
		try:
			self.client.delete_collection(name=name)
			self.collections.pop(name, None)
			self.logger.info(f"Deleted collection: {name}")

		except Exception as e:
			self.logger.error(f"Failed to delete collection '{name}': {e}")
			raise VectorStoreError(f"Collection deletion failed: {e}")

	async def list_collections(self) -> List[str]:
		"""List all ChromaDB collections.

		Returns:
		    List of collection names
		"""
		try:
			collections = self.client.list_collections()
			return [col.name for col in collections]
		except Exception as e:
			self.logger.error(f"Failed to list collections: {e}")
			return []

	async def collection_exists(self, name: str) -> bool:
		"""Check if collection exists.

		Args:
		    name: Collection name

		Returns:
		    True if collection exists
		"""
		try:
			collections = await self.list_collections()
			return name in collections
		except Exception as e:
			self.logger.error(f"Error checking collection existence: {e}")
			return False

	def _get_collection(self, name: str) -> chromadb.Collection:
		"""Get collection instance (cached or fetch).

		Args:
		    name: Collection name

		Returns:
		    ChromaDB collection instance
		"""
		if name not in self.collections:
			self.collections[name] = self.client.get_collection(name=name, embedding_function=self.embedding_function)
		return self.collections[name]

	async def add_embeddings(self, collection: str, batch: EmbeddingBatch) -> None:
		"""Add embeddings to ChromaDB collection.

		Args:
		    collection: Collection name
		    batch: Batch of embeddings to add
		"""
		try:
			col = self._get_collection(collection)

			col.add(ids=batch.ids, embeddings=batch.embeddings if batch.embeddings else None, documents=batch.documents, metadatas=batch.metadata)

			self.logger.debug(f"Added {len(batch.ids)} embeddings to collection '{collection}'")

		except Exception as e:
			self.logger.error(f"Failed to add embeddings: {e}")
			raise VectorStoreError(f"Add embeddings failed: {e}")

	async def update_embeddings(self, collection: str, batch: EmbeddingBatch) -> None:
		"""Update existing embeddings in collection.

		Args:
		    collection: Collection name
		    batch: Batch of embeddings to update
		"""
		try:
			col = self._get_collection(collection)

			col.update(ids=batch.ids, embeddings=batch.embeddings if batch.embeddings else None, documents=batch.documents, metadatas=batch.metadata)

			self.logger.debug(f"Updated {len(batch.ids)} embeddings in collection '{collection}'")

		except Exception as e:
			self.logger.error(f"Failed to update embeddings: {e}")
			raise VectorStoreError(f"Update embeddings failed: {e}")

	async def delete_embeddings(self, collection: str, ids: List[str]) -> int:
		"""Delete embeddings by IDs.

		Args:
		    collection: Collection name
		    ids: List of embedding IDs to delete

		Returns:
		    Number of embeddings deleted
		"""
		try:
			col = self._get_collection(collection)
			col.delete(ids=ids)

			self.logger.debug(f"Deleted {len(ids)} embeddings from collection '{collection}'")
			return len(ids)

		except Exception as e:
			self.logger.error(f"Failed to delete embeddings: {e}")
			raise VectorStoreError(f"Delete embeddings failed: {e}")

	async def get_embeddings(
		self, collection: str, ids: List[str], include_embeddings: bool = True, include_metadata: bool = True
	) -> List[Dict[str, Any]]:
		"""Retrieve embeddings by IDs.

		Args:
		    collection: Collection name
		    ids: List of embedding IDs
		    include_embeddings: Whether to include vectors
		    include_metadata: Whether to include metadata

		Returns:
		    List of embedding data dictionaries
		"""
		try:
			col = self._get_collection(collection)

			result = col.get(ids=ids, include=["documents", "metadatas", "embeddings"])

			# Transform ChromaDB result to standard format
			embeddings_list = []
			for i, doc_id in enumerate(result["ids"]):
				embedding_data = {"id": doc_id, "document": result["documents"][i] if "documents" in result else None}

				if include_metadata and "metadatas" in result:
					embedding_data["metadata"] = result["metadatas"][i]

				if include_embeddings and "embeddings" in result:
					embedding_data["embedding"] = result["embeddings"][i]

				embeddings_list.append(embedding_data)

			return embeddings_list

		except Exception as e:
			self.logger.error(f"Failed to get embeddings: {e}")
			raise VectorStoreError(f"Get embeddings failed: {e}")

	async def search(self, collection: str, query: SearchQuery) -> List[SearchResult]:
		"""Perform similarity search in ChromaDB.

		Args:
		    collection: Collection name
		    query: Search query with embedding and parameters

		Returns:
		    List of search results
		"""
		try:
			col = self._get_collection(collection)

			# Build where clause from filters
			where_clause = query.filters if query.filters else None

			result = col.query(
				query_embeddings=[query.query_embedding], n_results=query.limit, where=where_clause, include=["documents", "metadatas", "distances"]
			)

			# Transform to SearchResult objects
			search_results = []
			if result["ids"] and len(result["ids"]) > 0:
				for i, doc_id in enumerate(result["ids"][0]):
					# ChromaDB returns distances, convert to similarity score
					# Cosine distance: score = 1 - distance
					distance = result["distances"][0][i]
					score = 1.0 - distance if distance is not None else 0.0

					# Apply score threshold if specified
					if query.score_threshold and score < query.score_threshold:
						continue

					search_result = SearchResult(
						id=doc_id,
						score=score,
						distance=distance,
						metadata=result["metadatas"][0][i] if query.include_metadata else {},
						document=result["documents"][0][i],
					)
					search_results.append(search_result)

			return search_results

		except Exception as e:
			self.logger.error(f"Search failed in collection '{collection}': {e}")
			raise VectorStoreError(f"Search failed: {e}")

	async def batch_search(self, collection: str, queries: List[SearchQuery]) -> List[List[SearchResult]]:
		"""Perform multiple similarity searches.

		Args:
		    collection: Collection name
		    queries: List of search queries

		Returns:
		    List of result lists
		"""
		try:
			col = self._get_collection(collection)

			# Extract query embeddings
			query_embeddings = [q.query_embedding for q in queries]
			n_results = queries[0].limit if queries else 10

			result = col.query(query_embeddings=query_embeddings, n_results=n_results, include=["documents", "metadatas", "distances"])

			# Transform results for each query
			all_results = []
			for query_idx, query in enumerate(queries):
				query_results = []

				if result["ids"] and len(result["ids"]) > query_idx:
					for i, doc_id in enumerate(result["ids"][query_idx]):
						distance = result["distances"][query_idx][i]
						score = 1.0 - distance if distance is not None else 0.0

						if query.score_threshold and score < query.score_threshold:
							continue

						search_result = SearchResult(
							id=doc_id,
							score=score,
							distance=distance,
							metadata=result["metadatas"][query_idx][i] if query.include_metadata else {},
							document=result["documents"][query_idx][i],
						)
						query_results.append(search_result)

				all_results.append(query_results)

			return all_results

		except Exception as e:
			self.logger.error(f"Batch search failed: {e}")
			raise VectorStoreError(f"Batch search failed: {e}")

	async def count_embeddings(self, collection: str) -> int:
		"""Count total embeddings in collection.

		Args:
		    collection: Collection name

		Returns:
		    Total number of embeddings
		"""
		try:
			col = self._get_collection(collection)
			return col.count()
		except Exception as e:
			self.logger.error(f"Failed to count embeddings: {e}")
			return 0

	async def get_collection_info(self, collection: str) -> Dict[str, Any]:
		"""Get collection information and statistics.

		Args:
		    collection: Collection name

		Returns:
		    Dictionary with collection info
		"""
		try:
			col = self._get_collection(collection)

			return {"name": col.name, "count": col.count(), "metadata": col.metadata, "dimension": self.config.embedding_dimension}
		except Exception as e:
			self.logger.error(f"Failed to get collection info: {e}")
			return {}

	async def health_check(self) -> Dict[str, Any]:
		"""Check backend health status.

		Returns:
		    Health status dictionary
		"""
		try:
			if not self.client:
				return {"status": "unhealthy", "error": "Client not initialized"}

			# Try to list collections as health check
			collections = await self.list_collections()

			return {"status": "healthy", "backend": "chromadb", "collections_count": len(collections), "client_initialized": self.client is not None}

		except Exception as e:
			return {"status": "unhealthy", "backend": "chromadb", "error": str(e)}
