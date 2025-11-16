"""
Unit tests for VectorStoreBackend abstraction layer.

Tests abstract interface compliance, factory pattern, backend registration,
and mock backend implementation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vector_store_backend import (
	BackendType,
	EmbeddingBatch,
	SearchQuery,
	SearchResult,
	VectorStoreBackend,
	VectorStoreConfig,
	VectorStoreFactory,
)


class MockVectorBackend(VectorStoreBackend):
	"""Mock implementation of VectorStoreBackend for testing."""

	def __init__(self, config: VectorStoreConfig):
		self.config = config
		self._collections: Dict[str, List[Dict]] = {}
		self._connected = False

	async def connect(self) -> bool:
		"""Mock connection."""
		self._connected = True
		return True

	async def disconnect(self) -> None:
		"""Mock disconnection."""
		self._connected = False

	async def create_collection(self, name: str, embedding_dimension: int, metadata: Optional[Dict] = None) -> bool:
		"""Mock collection creation."""
		if name in self._collections:
			return False
		self._collections[name] = []
		return True

	async def delete_collection(self, name: str) -> bool:
		"""Mock collection deletion."""
		if name in self._collections:
			del self._collections[name]
			return True
		return False

	async def list_collections(self) -> List[str]:
		"""Mock list collections."""
		return list(self._collections.keys())

	async def collection_exists(self, name: str) -> bool:
		"""Mock collection existence check."""
		return name in self._collections

	async def get_collection_info(self, name: str) -> Optional[Dict]:
		"""Mock get collection info."""
		if name not in self._collections:
			return None
		return {
			"name": name,
			"count": len(self._collections[name]),
			"dimension": 384,  # Mock dimension
		}

	async def add_embeddings(self, batch: EmbeddingBatch) -> List[str]:
		"""Mock add embeddings."""
		if batch.collection_name not in self._collections:
			await self.create_collection(batch.collection_name, 384)

		ids = []
		for i, (emb, meta, text) in enumerate(zip(batch.embeddings, batch.metadata_list, batch.texts)):
			doc_id = f"doc_{len(self._collections[batch.collection_name])}_{i}"
			self._collections[batch.collection_name].append(
				{
					"id": doc_id,
					"embedding": emb,
					"metadata": meta,
					"text": text,
				}
			)
			ids.append(doc_id)
		return ids

	async def search(self, query: SearchQuery) -> List[SearchResult]:
		"""Mock search."""
		if query.collection_name not in self._collections:
			return []

		# Simple mock: return first n results
		results = []
		for doc in self._collections[query.collection_name][: query.limit]:
			results.append(
				SearchResult(
					id=doc["id"],
					score=0.95,  # Mock score
					metadata=doc["metadata"],
					text=doc.get("text", ""),
				)
			)
		return results

	async def get_by_id(self, collection_name: str, ids: List[str]) -> List[Optional[Dict]]:
		"""Mock get by ID."""
		if collection_name not in self._collections:
			return [None] * len(ids)

		results = []
		id_set = set(ids)
		for doc in self._collections[collection_name]:
			if doc["id"] in id_set:
				results.append(doc)
		return results

	async def update_embedding(self, collection_name: str, doc_id: str, embedding: List[float], metadata: Optional[Dict] = None) -> bool:
		"""Mock update embedding."""
		if collection_name not in self._collections:
			return False

		for doc in self._collections[collection_name]:
			if doc["id"] == doc_id:
				doc["embedding"] = embedding
				if metadata:
					doc["metadata"] = metadata
				return True
		return False

	async def delete_embeddings(self, collection_name: str, ids: List[str]) -> int:
		"""Mock delete embeddings."""
		if collection_name not in self._collections:
			return 0

		id_set = set(ids)
		original_count = len(self._collections[collection_name])
		self._collections[collection_name] = [doc for doc in self._collections[collection_name] if doc["id"] not in id_set]
		return original_count - len(self._collections[collection_name])

	async def count_embeddings(self, collection_name: str) -> int:
		"""Mock count embeddings."""
		if collection_name not in self._collections:
			return 0
		return len(self._collections[collection_name])

	async def clear_collection(self, collection_name: str) -> bool:
		"""Mock clear collection."""
		if collection_name not in self._collections:
			return False
		self._collections[collection_name] = []
		return True

	async def health_check(self) -> Dict[str, any]:
		"""Mock health check."""
		return {
			"status": "healthy" if self._connected else "disconnected",
			"backend": "mock",
			"collections": len(self._collections),
		}

	async def get_statistics(self, collection_name: str) -> Dict[str, any]:
		"""Mock get statistics."""
		if collection_name not in self._collections:
			return {}

		return {
			"collection_name": collection_name,
			"total_embeddings": len(self._collections[collection_name]),
			"dimension": 384,
		}

	async def batch_search(self, queries: List[SearchQuery]) -> List[List[SearchResult]]:
		"""Mock batch search."""
		results = []
		for query in queries:
			results.append(await self.search(query))
		return results

	async def export_collection(self, collection_name: str, output_path: str) -> bool:
		"""Mock export collection."""
		return collection_name in self._collections

	async def import_collection(self, collection_name: str, input_path: str) -> bool:
		"""Mock import collection."""
		# Just create empty collection
		return await self.create_collection(collection_name, 384)


class TestVectorStoreConfig:
	"""Test VectorStoreConfig dataclass."""

	def test_config_creation(self):
		"""Test creating configuration."""
		config = VectorStoreConfig(
			backend_type=BackendType.CHROMADB,
			host="localhost",
			port=8000,
			collection_name="test_collection",
		)

		assert config.backend_type == BackendType.CHROMADB
		assert config.host == "localhost"
		assert config.port == 8000
		assert config.collection_name == "test_collection"

	def test_config_with_api_key(self):
		"""Test configuration with API key."""
		config = VectorStoreConfig(
			backend_type=BackendType.PINECONE,
			api_key="test-api-key",
			collection_name="vectors",
		)

		assert config.api_key == "test-api-key"
		assert config.backend_type == BackendType.PINECONE


class TestEmbeddingBatch:
	"""Test EmbeddingBatch dataclass."""

	def test_batch_creation(self):
		"""Test creating embedding batch."""
		batch = EmbeddingBatch(
			collection_name="test_collection",
			embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
			metadata_list=[{"source": "doc1"}, {"source": "doc2"}],
			texts=["Text 1", "Text 2"],
		)

		assert batch.collection_name == "test_collection"
		assert len(batch.embeddings) == 2
		assert len(batch.metadata_list) == 2
		assert len(batch.texts) == 2


class TestSearchQuery:
	"""Test SearchQuery dataclass."""

	def test_query_creation(self):
		"""Test creating search query."""
		query = SearchQuery(
			collection_name="test_collection",
			query_embedding=[0.1, 0.2, 0.3],
			limit=10,
			filters={"category": "tech"},
		)

		assert query.collection_name == "test_collection"
		assert len(query.query_embedding) == 3
		assert query.limit == 10
		assert query.filters["category"] == "tech"


class TestSearchResult:
	"""Test SearchResult dataclass."""

	def test_result_creation(self):
		"""Test creating search result."""
		result = SearchResult(
			id="doc_1",
			score=0.95,
			metadata={"source": "test"},
			text="Sample text",
		)

		assert result.id == "doc_1"
		assert result.score == 0.95
		assert result.metadata["source"] == "test"
		assert result.text == "Sample text"


class TestVectorStoreFactory:
	"""Test VectorStoreFactory pattern."""

	def test_register_backend(self):
		"""Test registering a new backend."""
		VectorStoreFactory.register_backend("mock", MockVectorBackend)

		assert "mock" in VectorStoreFactory._backends
		assert VectorStoreFactory._backends["mock"] == MockVectorBackend

	def test_create_backend(self):
		"""Test creating backend instance."""
		VectorStoreFactory.register_backend("mock", MockVectorBackend)

		config = VectorStoreConfig(
			backend_type="mock",
			collection_name="test",
		)

		backend = VectorStoreFactory.create_backend(config)

		assert isinstance(backend, MockVectorBackend)
		assert backend.config == config

	def test_create_unregistered_backend_raises_error(self):
		"""Test creating unregistered backend raises ValueError."""
		config = VectorStoreConfig(
			backend_type="nonexistent",
			collection_name="test",
		)

		with pytest.raises(ValueError) as exc_info:
			VectorStoreFactory.create_backend(config)

		assert "Unknown backend type" in str(exc_info.value)

	def test_list_available_backends(self):
		"""Test listing available backends."""
		VectorStoreFactory.register_backend("mock", MockVectorBackend)

		backends = VectorStoreFactory.list_backends()

		assert "mock" in backends
		assert isinstance(backends, list)


class TestMockBackendOperations:
	"""Test MockVectorBackend operations."""

	@pytest.fixture
	def backend(self):
		"""Create mock backend instance."""
		VectorStoreFactory.register_backend("mock", MockVectorBackend)
		config = VectorStoreConfig(
			backend_type="mock",
			collection_name="test_collection",
		)
		return VectorStoreFactory.create_backend(config)

	@pytest.mark.asyncio
	async def test_connect_disconnect(self, backend):
		"""Test connection lifecycle."""
		assert await backend.connect() is True
		assert backend._connected is True

		await backend.disconnect()
		assert backend._connected is False

	@pytest.mark.asyncio
	async def test_create_collection(self, backend):
		"""Test creating collection."""
		await backend.connect()

		result = await backend.create_collection("new_collection", 384)

		assert result is True
		assert "new_collection" in backend._collections

	@pytest.mark.asyncio
	async def test_delete_collection(self, backend):
		"""Test deleting collection."""
		await backend.connect()
		await backend.create_collection("temp_collection", 384)

		result = await backend.delete_collection("temp_collection")

		assert result is True
		assert "temp_collection" not in backend._collections

	@pytest.mark.asyncio
	async def test_list_collections(self, backend):
		"""Test listing collections."""
		await backend.connect()
		await backend.create_collection("collection1", 384)
		await backend.create_collection("collection2", 384)

		collections = await backend.list_collections()

		assert len(collections) == 2
		assert "collection1" in collections
		assert "collection2" in collections

	@pytest.mark.asyncio
	async def test_collection_exists(self, backend):
		"""Test checking collection existence."""
		await backend.connect()
		await backend.create_collection("exists", 384)

		assert await backend.collection_exists("exists") is True
		assert await backend.collection_exists("not_exists") is False

	@pytest.mark.asyncio
	async def test_add_embeddings(self, backend):
		"""Test adding embeddings."""
		await backend.connect()
		await backend.create_collection("embeddings", 384)

		batch = EmbeddingBatch(
			collection_name="embeddings",
			embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
			metadata_list=[{"id": 1}, {"id": 2}],
			texts=["Text 1", "Text 2"],
		)

		ids = await backend.add_embeddings(batch)

		assert len(ids) == 2
		assert all(isinstance(doc_id, str) for doc_id in ids)

	@pytest.mark.asyncio
	async def test_search_embeddings(self, backend):
		"""Test searching embeddings."""
		await backend.connect()
		await backend.create_collection("search", 384)

		# Add some embeddings
		batch = EmbeddingBatch(
			collection_name="search",
			embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
			metadata_list=[{"id": 1}, {"id": 2}],
			texts=["Text 1", "Text 2"],
		)
		await backend.add_embeddings(batch)

		# Search
		query = SearchQuery(
			collection_name="search",
			query_embedding=[0.1, 0.2, 0.3],
			limit=2,
		)

		results = await backend.search(query)

		assert len(results) <= 2
		assert all(isinstance(r, SearchResult) for r in results)

	@pytest.mark.asyncio
	async def test_count_embeddings(self, backend):
		"""Test counting embeddings."""
		await backend.connect()
		await backend.create_collection("count", 384)

		batch = EmbeddingBatch(
			collection_name="count",
			embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
			metadata_list=[{}, {}, {}],
			texts=["Text 1", "Text 2", "Text 3"],
		)
		await backend.add_embeddings(batch)

		count = await backend.count_embeddings("count")

		assert count == 3

	@pytest.mark.asyncio
	async def test_clear_collection(self, backend):
		"""Test clearing collection."""
		await backend.connect()
		await backend.create_collection("clear", 384)

		# Add embeddings
		batch = EmbeddingBatch(
			collection_name="clear",
			embeddings=[[0.1, 0.2, 0.3]],
			metadata_list=[{}],
			texts=["Text"],
		)
		await backend.add_embeddings(batch)

		# Clear
		result = await backend.clear_collection("clear")

		assert result is True
		assert await backend.count_embeddings("clear") == 0

	@pytest.mark.asyncio
	async def test_health_check(self, backend):
		"""Test health check."""
		await backend.connect()

		health = await backend.health_check()

		assert health["status"] == "healthy"
		assert health["backend"] == "mock"
		assert "collections" in health

	@pytest.mark.asyncio
	async def test_get_statistics(self, backend):
		"""Test getting collection statistics."""
		await backend.connect()
		await backend.create_collection("stats", 384)

		batch = EmbeddingBatch(
			collection_name="stats",
			embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
			metadata_list=[{}, {}],
			texts=["Text 1", "Text 2"],
		)
		await backend.add_embeddings(batch)

		stats = await backend.get_statistics("stats")

		assert stats["collection_name"] == "stats"
		assert stats["total_embeddings"] == 2
		assert "dimension" in stats


class TestAbstractInterfaceCompliance:
	"""Test that MockVectorBackend properly implements abstract interface."""

	@pytest.mark.asyncio
	async def test_implements_all_abstract_methods(self):
		"""Test mock backend implements all required methods."""
		config = VectorStoreConfig(
			backend_type="mock",
			collection_name="test",
		)
		backend = MockVectorBackend(config)

		# Check all abstract methods are implemented
		required_methods = [
			"connect",
			"disconnect",
			"create_collection",
			"delete_collection",
			"list_collections",
			"collection_exists",
			"get_collection_info",
			"add_embeddings",
			"search",
			"get_by_id",
			"update_embedding",
			"delete_embeddings",
			"count_embeddings",
			"clear_collection",
			"health_check",
			"get_statistics",
			"batch_search",
			"export_collection",
			"import_collection",
		]

		for method_name in required_methods:
			assert hasattr(backend, method_name)
			assert callable(getattr(backend, method_name))
