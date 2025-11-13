"""
Performance optimization service for large contract processing.

This module provides optimizations for:
- Large file processing with chunking
- Memory management and cleanup
- Concurrent processing
- Caching mechanisms
- Database query optimization
"""

import asyncio
import gc
import hashlib
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.monitoring import monitor_performance

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class ProcessingMetrics:
	"""Metrics for processing performance."""

	start_time: float
	end_time: float
	memory_usage_mb: float
	cpu_usage_percent: float
	chunks_processed: int
	total_chunks: int
	cache_hits: int
	cache_misses: int


class MemoryManager:
	"""Advanced memory management for large document processing."""

	def __init__(self, max_memory_mb: int = 2048, cleanup_threshold: float = 0.8):
		self.max_memory_mb = max_memory_mb
		self.cleanup_threshold = cleanup_threshold
		self.temp_files: Dict[str, str] = {}
		self.memory_usage_history: List[float] = []

	def get_memory_usage(self) -> Dict[str, float]:
		"""Get current memory usage statistics."""
		process = psutil.Process()
		memory_info = process.memory_info()

		return {
			"rss_mb": memory_info.rss / 1024 / 1024,
			"vms_mb": memory_info.vms / 1024 / 1024,
			"percent": process.memory_percent(),
			"available_mb": psutil.virtual_memory().available / 1024 / 1024,
		}

	def should_cleanup(self) -> bool:
		"""Check if memory cleanup is needed."""
		memory_usage = self.get_memory_usage()
		return memory_usage["percent"] > (self.cleanup_threshold * 100)

	def cleanup_memory(self) -> int:
		"""Perform memory cleanup and return number of items cleaned."""
		cleaned_items = 0

		# Force garbage collection
		collected = gc.collect()
		cleaned_items += collected

		# Clean up temporary files
		for file_id, file_path in list(self.temp_files.items()):
			try:
				if os.path.exists(file_path):
					os.remove(file_path)
					del self.temp_files[file_id]
					cleaned_items += 1
			except Exception as e:
				logger.warning(f"Failed to clean up temp file {file_path}: {e}")

		# Record memory usage
		memory_usage = self.get_memory_usage()
		self.memory_usage_history.append(memory_usage["rss_mb"])

		# Keep only last 100 measurements
		if len(self.memory_usage_history) > 100:
			self.memory_usage_history = self.memory_usage_history[-100:]

		logger.info(f"Memory cleanup completed: {cleaned_items} items, {memory_usage['rss_mb']:.1f}MB used")
		return cleaned_items

	def create_temp_file(self, content: bytes, extension: str = ".tmp") -> Tuple[str, str]:
		"""Create a temporary file and return (file_id, file_path)."""
		file_id = hashlib.md5(content).hexdigest()[:16]
		temp_dir = Path(settings.temp_directory)
		temp_dir.mkdir(exist_ok=True)

		file_path = temp_dir / f"{file_id}{extension}"

		with open(file_path, "wb") as f:
			f.write(content)

		self.temp_files[file_id] = str(file_path)
		return file_id, str(file_path)

	def cleanup_temp_file(self, file_id: str) -> bool:
		"""Clean up a specific temporary file."""
		if file_id in self.temp_files:
			file_path = self.temp_files[file_id]
			try:
				if os.path.exists(file_path):
					os.remove(file_path)
				del self.temp_files[file_id]
				return True
			except Exception as e:
				logger.warning(f"Failed to clean up temp file {file_path}: {e}")
		return False


class DocumentChunker:
	"""Advanced document chunking for large files."""

	def __init__(self, chunk_size: int = 10000, chunk_overlap: int = 1000):
		self.chunk_size = chunk_size
		self.chunk_overlap = chunk_overlap
		self.text_splitter = RecursiveCharacterTextSplitter(
			chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len, separators=["\n\n", "\n", " ", ""]
		)

	def chunk_document(self, text: str) -> List[str]:
		"""Split document into chunks."""
		return self.text_splitter.split_text(text)

	def chunk_document_with_metadata(self, text: str, metadata: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
		"""Split document into chunks with metadata."""
		chunks = self.chunk_document(text)

		result = []
		for i, chunk in enumerate(chunks):
			chunk_metadata = (metadata or {}).copy()
			chunk_metadata.update({"chunk_index": i, "total_chunks": len(chunks), "chunk_size": len(chunk)})
			result.append({"text": chunk, "metadata": chunk_metadata})

		return result

	def process_large_document(self, text: str, max_chunk_size: int | None = None) -> List[Dict[str, Any]]:
		"""Process very large documents with adaptive chunking."""
		if max_chunk_size and len(text) > max_chunk_size:
			# For very large documents, use smaller chunks
			original_chunk_size = self.chunk_size
			self.chunk_size = min(self.chunk_size, max_chunk_size // 10)

			try:
				result = self.chunk_document_with_metadata(text)
			finally:
				self.chunk_size = original_chunk_size
		else:
			result = self.chunk_document_with_metadata(text)

		return result


class EmbeddingCache:
	"""LRU cache for document embeddings to avoid recomputation."""

	def __init__(self, max_size: int = 1000):
		self.max_size = max_size
		self.cache: Dict[str, List[float]] = {}
		self.access_times: Dict[str, float] = {}

	def _evict_oldest(self):
		"""Evict the least recently used item."""
		if not self.cache:
			return

		oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
		del self.cache[oldest_key]
		del self.access_times[oldest_key]

	def get_embedding(self, text: str, embedding_model) -> List[float]:
		"""Get embedding from cache or compute if not cached."""
		text_hash = hashlib.md5(text.encode()).hexdigest()

		if text_hash in self.cache:
			self.access_times[text_hash] = time.time()
			return self.cache[text_hash]

		# Compute embedding
		embedding = embedding_model.embed_query(text)

		# Add to cache
		if len(self.cache) >= self.max_size:
			self._evict_oldest()

		self.cache[text_hash] = embedding
		self.access_times[text_hash] = time.time()

		return embedding

	def clear_cache(self):
		"""Clear the entire cache."""
		self.cache.clear()
		self.access_times.clear()

	def get_cache_stats(self) -> Dict[str, Any]:
		"""Get cache statistics."""
		return {"size": len(self.cache), "max_size": self.max_size, "hit_rate": getattr(self, "_hit_rate", 0.0)}


class ConcurrentProcessor:
	"""Concurrent processing for multiple documents."""

	def __init__(self, max_workers: int = 4, use_processes: bool = False):
		self.max_workers = max_workers
		self.use_processes = use_processes
		self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

	async def process_documents_concurrently(self, documents: List[Dict[str, Any]], process_func: callable) -> List[Any]:
		"""Process multiple documents concurrently."""
		loop = asyncio.get_event_loop()

		with self.executor_class(max_workers=self.max_workers) as executor:
			tasks = [loop.run_in_executor(executor, process_func, doc) for doc in documents]

			results = await asyncio.gather(*tasks, return_exceptions=True)

			# Filter out exceptions
			valid_results = [r for r in results if not isinstance(r, Exception)]
			exceptions = [r for r in results if isinstance(r, Exception)]

			if exceptions:
				logger.warning(f"Processed {len(valid_results)} documents, {len(exceptions)} failed")

			return valid_results

	def process_documents_sync(self, documents: List[Dict[str, Any]], process_func: callable) -> List[Any]:
		"""Process multiple documents concurrently (synchronous)."""
		with self.executor_class(max_workers=self.max_workers) as executor:
			futures = [executor.submit(process_func, doc) for doc in documents]
			results = [future.result() for future in futures]
			return results


class DatabaseOptimizer:
	"""Database query optimization utilities."""

	def __init__(self, batch_size: int = 100):
		self.batch_size = batch_size

	async def batch_insert_contracts(self, contracts: List[Dict[str, Any]], db_manager) -> int:
		"""Insert contracts in batches for better performance."""
		total_inserted = 0

		for i in range(0, len(contracts), self.batch_size):
			batch = contracts[i : i + self.batch_size]

			try:
				# Use batch insert if available
				if hasattr(db_manager, "batch_insert_contracts"):
					inserted = await db_manager.batch_insert_contracts(batch)
				else:
					# Fallback to individual inserts
					inserted = 0
					for contract in batch:
						await db_manager.insert_contract(contract)
						inserted += 1

				total_inserted += inserted
				logger.debug(f"Inserted batch {i // self.batch_size + 1}: {inserted} contracts")

			except Exception as e:
				logger.error(f"Failed to insert batch {i // self.batch_size + 1}: {e}")
				# Continue with next batch
				continue

		return total_inserted

	async def batch_update_contracts(self, updates: List[Dict[str, Any]], db_manager) -> int:
		"""Update contracts in batches."""
		total_updated = 0

		for i in range(0, len(updates), self.batch_size):
			batch = updates[i : i + self.batch_size]

			try:
				if hasattr(db_manager, "batch_update_contracts"):
					updated = await db_manager.batch_update_contracts(batch)
				else:
					updated = 0
					for update in batch:
						await db_manager.update_contract(update["id"], update)
						updated += 1

				total_updated += updated

			except Exception as e:
				logger.error(f"Failed to update batch {i // self.batch_size + 1}: {e}")
				continue

		return total_updated


class PerformanceOptimizer:
	"""Main performance optimization service."""

	def __init__(self):
		self.memory_manager = MemoryManager()
		self.document_chunker = DocumentChunker()
		self.embedding_cache = EmbeddingCache()
		self.concurrent_processor = ConcurrentProcessor()
		self.db_optimizer = DatabaseOptimizer()

		# Initialize embedding model
		api_key = settings.openai_api_key
		if hasattr(api_key, "get_secret_value"):
			api_key = api_key.get_secret_value()
		self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)

	@monitor_performance("large_document_processing", "performance_optimizer")
	async def process_large_contract(
		self, contract_text: str, contract_filename: str, chunk_size: int | None = None, enable_caching: bool = True
	) -> Dict[str, Any]:
		"""Process large contract with performance optimizations."""
		start_time = time.time()
		start_memory = self.memory_manager.get_memory_usage()

		try:
			# Check memory usage and cleanup if needed
			if self.memory_manager.should_cleanup():
				logger.info("Memory cleanup triggered before processing")
				self.memory_manager.cleanup_memory()

			# Chunk the document
			if chunk_size:
				self.document_chunker.chunk_size = chunk_size

			chunks = self.document_chunker.process_large_document(contract_text, max_chunk_size=chunk_size)

			logger.info(f"Document chunked into {len(chunks)} pieces")

			# Process chunks concurrently
			processed_chunks = await self._process_chunks_concurrently(chunks, enable_caching)

			# Combine results
			combined_result = self._combine_chunk_results(processed_chunks)

			# Add processing metadata
			end_time = time.time()
			end_memory = self.memory_manager.get_memory_usage()

			combined_result.update(
				{
					"processing_metrics": {
						"total_time": end_time - start_time,
						"memory_usage_mb": end_memory["rss_mb"] - start_memory["rss_mb"],
						"chunks_processed": len(processed_chunks),
						"total_chunks": len(chunks),
						"cache_hits": getattr(self.embedding_cache, "_cache_hits", 0),
						"cache_misses": getattr(self.embedding_cache, "_cache_misses", 0),
					}
				}
			)

			return combined_result

		except Exception as e:
			logger.error(f"Error processing large contract: {e}")
			raise
		finally:
			# Cleanup memory after processing
			self.memory_manager.cleanup_memory()

	async def _process_chunks_concurrently(self, chunks: List[Dict[str, Any]], enable_caching: bool) -> List[Dict[str, Any]]:
		"""Process document chunks concurrently."""

		async def process_chunk(chunk_data: Dict[str, Any]) -> Dict[str, Any]:
			"""Process a single chunk."""
			chunk_text = chunk_data["text"]
			chunk_metadata = chunk_data["metadata"]

			# Get embedding (with caching if enabled)
			if enable_caching:
				embedding = self.embedding_cache.get_embedding(chunk_text, self.embedding_model)
			else:
				embedding = self.embedding_model.embed_query(chunk_text)

			# Analyze chunk for risky clauses (simplified)
			risky_clauses = self._analyze_chunk_for_risks(chunk_text)

			return {"text": chunk_text, "embedding": embedding, "risky_clauses": risky_clauses, "metadata": chunk_metadata}

		# Process chunks concurrently
		processed_chunks = await self.concurrent_processor.process_documents_concurrently(chunks, process_chunk)

		return processed_chunks

	def _analyze_chunk_for_risks(self, chunk_text: str) -> List[Dict[str, Any]]:
		"""Analyze a chunk for risky clauses (simplified implementation)."""
		# This is a simplified implementation
		# In practice, you would use the full job application tracking workflow

		risky_keywords = ["liability", "damages", "indemnification", "warranty", "termination", "penalty", "exclusive", "non-compete"]

		risky_clauses = []
		sentences = chunk_text.split(".")

		for i, sentence in enumerate(sentences):
			if any(keyword in sentence.lower() for keyword in risky_keywords):
				risky_clauses.append(
					{
						"clause_text": sentence.strip(),
						"risk_level": "Medium",  # Simplified
						"chunk_index": i,
					}
				)

		return risky_clauses

	def _combine_chunk_results(self, processed_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""Combine results from processed chunks."""
		all_risky_clauses = []
		all_embeddings = []

		for chunk in processed_chunks:
			all_risky_clauses.extend(chunk["risky_clauses"])
			all_embeddings.append(chunk["embedding"])

		# Calculate overall risk score
		total_clauses = sum(len(chunk["text"].split(".")) for chunk in processed_chunks)
		risk_score = len(all_risky_clauses) / total_clauses if total_clauses > 0 else 0.0

		return {
			"risky_clauses": all_risky_clauses,
			"overall_risk_score": risk_score,
			"total_chunks": len(processed_chunks),
			"total_clauses": total_clauses,
			"embeddings": all_embeddings,
		}

	async def batch_process_contracts(self, contracts: List[Dict[str, Any]], max_concurrent: int = 5) -> List[Dict[str, Any]]:
		"""Process multiple contracts in batches with concurrency control."""
		results = []

		# Process contracts in batches to control memory usage
		for i in range(0, len(contracts), max_concurrent):
			batch = contracts[i : i + max_concurrent]

			# Process batch concurrently
			batch_tasks = [self.process_large_contract(contract["text"], contract["filename"]) for contract in batch]

			batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

			# Add successful results
			for result in batch_results:
				if not isinstance(result, Exception):
					results.append(result)
				else:
					logger.error(f"Contract processing failed: {result}")

			# Cleanup memory between batches
			self.memory_manager.cleanup_memory()

		return results

	def get_performance_stats(self) -> Dict[str, Any]:
		"""Get performance statistics."""
		memory_stats = self.memory_manager.get_memory_usage()
		cache_stats = self.embedding_cache.get_cache_stats()

		return {
			"memory_usage": memory_stats,
			"cache_stats": cache_stats,
			"memory_history": self.memory_manager.memory_usage_history[-10:],  # Last 10 measurements
			"temp_files_count": len(self.memory_manager.temp_files),
		}

	def optimize_for_large_files(self, file_size_mb: int) -> Dict[str, Any]:
		"""Optimize settings for large file processing."""
		optimizations = {}

		if file_size_mb > 100:  # Very large files
			optimizations.update(
				{
					"chunk_size": 5000,  # Smaller chunks
					"chunk_overlap": 500,
					"max_concurrent": 2,  # Reduce concurrency
					"enable_caching": True,
					"memory_cleanup_frequency": "every_chunk",
				}
			)
		elif file_size_mb > 50:  # Large files
			optimizations.update(
				{"chunk_size": 8000, "chunk_overlap": 800, "max_concurrent": 3, "enable_caching": True, "memory_cleanup_frequency": "every_batch"}
			)
		else:  # Normal files
			optimizations.update(
				{
					"chunk_size": 10000,
					"chunk_overlap": 1000,
					"max_concurrent": 5,
					"enable_caching": True,
					"memory_cleanup_frequency": "end_of_processing",
				}
			)

		# Apply optimizations
		self.document_chunker.chunk_size = optimizations["chunk_size"]
		self.document_chunker.chunk_overlap = optimizations["chunk_overlap"]
		self.concurrent_processor.max_workers = optimizations["max_concurrent"]

		logger.info(f"Optimized settings for {file_size_mb}MB file: {optimizations}")
		return optimizations


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
