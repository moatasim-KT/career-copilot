"""
Advanced memory management system for the contract analyzer application.
Provides memory monitoring, cleanup, and optimization features.
"""

import gc
import logging
import os
import threading
import time
import weakref
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


class MemoryManager:
	"""Advanced memory management with monitoring and cleanup."""

	def __init__(self):
		self.process = psutil.Process()
		self.memory_threshold = 0.8  # 80% memory usage threshold
		self.cleanup_interval = 300  # 5 minutes
		self.monitoring_enabled = True
		self.cleanup_callbacks: List[Callable] = []
		self.tracked_objects: Set[weakref.ref] = set()
		self.memory_stats = {"peak_memory": 0, "current_memory": 0, "cleanup_count": 0, "last_cleanup": None, "memory_warnings": 0}

		# Start monitoring thread
		self._start_monitoring()

	def _start_monitoring(self):
		"""Start background memory monitoring thread."""
		if self.monitoring_enabled:
			monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
			monitor_thread.start()
			logger.info("Memory monitoring started")

	def _monitor_memory(self):
		"""Background memory monitoring loop."""
		while self.monitoring_enabled:
			try:
				self._check_memory_usage()
				time.sleep(60)  # Check every minute
			except Exception as e:
				logger.error(f"Memory monitoring error: {e}")
				time.sleep(60)

	def _check_memory_usage(self):
		"""Check current memory usage and trigger cleanup if needed."""
		try:
			memory_info = self.process.memory_info()
			memory_percent = memory_info.rss / psutil.virtual_memory().total

			self.memory_stats["current_memory"] = memory_info.rss
			self.memory_stats["peak_memory"] = max(self.memory_stats["peak_memory"], memory_info.rss)

			if memory_percent > self.memory_threshold:
				logger.warning(f"High memory usage: {memory_percent:.2%}")
				self.memory_stats["memory_warnings"] += 1
				self._trigger_cleanup()

		except Exception as e:
			logger.error(f"Memory check error: {e}")

	def _trigger_cleanup(self):
		"""Trigger memory cleanup procedures."""
		try:
			logger.info("Triggering memory cleanup")

			# Run registered cleanup callbacks
			for callback in self.cleanup_callbacks:
				try:
					callback()
				except Exception as e:
					logger.error(f"Cleanup callback error: {e}")

			# Force garbage collection
			collected = gc.collect()
			logger.info(f"Garbage collection freed {collected} objects")

			# Clean up tracked objects
			self._cleanup_tracked_objects()

			self.memory_stats["cleanup_count"] += 1
			self.memory_stats["last_cleanup"] = datetime.utcnow()

		except Exception as e:
			logger.error(f"Memory cleanup error: {e}")

	def _cleanup_tracked_objects(self):
		"""Clean up tracked objects that are no longer referenced."""
		dead_refs = []
		for ref in self.tracked_objects:
			if ref() is None:
				dead_refs.append(ref)

		for ref in dead_refs:
			self.tracked_objects.discard(ref)

		if dead_refs:
			logger.info(f"Cleaned up {len(dead_refs)} dead object references")

	def track_object(self, obj: Any) -> weakref.ref:
		"""Track an object for memory management."""
		ref = weakref.ref(obj)
		self.tracked_objects.add(ref)
		return ref

	def add_cleanup_callback(self, callback: Callable):
		"""Add a cleanup callback function."""
		self.cleanup_callbacks.append(callback)
		logger.info(f"Added cleanup callback: {callback.__name__}")

	def remove_cleanup_callback(self, callback: Callable):
		"""Remove a cleanup callback function."""
		if callback in self.cleanup_callbacks:
			self.cleanup_callbacks.remove(callback)
			logger.info(f"Removed cleanup callback: {callback.__name__}")

	def get_memory_stats(self) -> Dict[str, Any]:
		"""Get current memory statistics."""
		try:
			memory_info = self.process.memory_info()
			virtual_memory = psutil.virtual_memory()

			return {
				"process_memory_rss": memory_info.rss,
				"process_memory_vms": memory_info.vms,
				"process_memory_percent": memory_info.rss / virtual_memory.total,
				"system_memory_total": virtual_memory.total,
				"system_memory_available": virtual_memory.available,
				"system_memory_percent": virtual_memory.percent,
				"tracked_objects": len(self.tracked_objects),
				"cleanup_callbacks": len(self.cleanup_callbacks),
				**self.memory_stats,
			}
		except Exception as e:
			logger.error(f"Error getting memory stats: {e}")
			return self.memory_stats

	def force_cleanup(self):
		"""Force immediate memory cleanup."""
		logger.info("Forcing memory cleanup")
		self._trigger_cleanup()

	def set_memory_threshold(self, threshold: float):
		"""Set memory usage threshold for cleanup triggers."""
		if 0 < threshold <= 1:
			self.memory_threshold = threshold
			logger.info(f"Memory threshold set to {threshold:.2%}")
		else:
			raise ValueError("Memory threshold must be between 0 and 1")

	def stop_monitoring(self):
		"""Stop memory monitoring."""
		self.monitoring_enabled = False
		logger.info("Memory monitoring stopped")


class MemoryContext:
	"""Context manager for memory-aware operations."""

	def __init__(self, memory_manager: MemoryManager, operation_name: str):
		self.memory_manager = memory_manager
		self.operation_name = operation_name
		self.start_memory = 0
		self.start_time = 0

	def __enter__(self):
		self.start_time = time.time()
		self.start_memory = self.memory_manager.process.memory_info().rss
		logger.debug(f"Starting {self.operation_name} - Memory: {self.start_memory / 1024 / 1024:.2f} MB")
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		end_time = time.time()
		end_memory = self.memory_manager.process.memory_info().rss

		duration = end_time - self.start_time
		memory_delta = end_memory - self.start_memory

		logger.debug(f"Completed {self.operation_name} - Duration: {duration:.2f}s, Memory delta: {memory_delta / 1024 / 1024:.2f} MB")

		# Trigger cleanup if memory usage increased significantly
		if memory_delta > 100 * 1024 * 1024:  # 100MB increase
			logger.warning(f"High memory usage in {self.operation_name}: {memory_delta / 1024 / 1024:.2f} MB")
			self.memory_manager._trigger_cleanup()


class FileMemoryManager:
	"""Memory management for file operations."""

	def __init__(self, memory_manager: MemoryManager):
		self.memory_manager = memory_manager
		self.open_files: Dict[str, Any] = {}
		self.file_cache: Dict[str, bytes] = {}
		self.max_cache_size = 500 * 1024 * 1024  # 500MB
		self.current_cache_size = 0

	def open_file(self, file_path: str, mode: str = "rb") -> Any:
		"""Open a file with memory tracking."""
		if file_path in self.open_files:
			return self.open_files[file_path]

		try:
			file_obj = open(file_path, mode)
			self.open_files[file_path] = file_obj
			self.memory_manager.track_object(file_obj)
			return file_obj
		except Exception as e:
			logger.error(f"Error opening file {file_path}: {e}")
			raise

	def close_file(self, file_path: str):
		"""Close a file and clean up resources."""
		if file_path in self.open_files:
			try:
				self.open_files[file_path].close()
				del self.open_files[file_path]
			except Exception as e:
				logger.error(f"Error closing file {file_path}: {e}")

	def read_file_chunked(self, file_path: str, chunk_size: int = 8192) -> bytes:
		"""Read a file in chunks to manage memory usage."""
		content = b""
		try:
			with self.open_file(file_path, "rb") as f:
				while True:
					chunk = f.read(chunk_size)
					if not chunk:
						break
					content += chunk

					# Check memory usage periodically
					if len(content) % (chunk_size * 100) == 0:  # Every 100 chunks
						self.memory_manager._check_memory_usage()

			return content
		except Exception as e:
			logger.error(f"Error reading file {file_path}: {e}")
			raise

	def cache_file_content(self, file_path: str, content: bytes) -> bool:
		"""Cache file content with size limits."""
		if self.current_cache_size + len(content) > self.max_cache_size:
			# Remove oldest entries to make space
			self._evict_cache_entries(len(content))

		self.file_cache[file_path] = content
		self.current_cache_size += len(content)
		return True

	def get_cached_content(self, file_path: str) -> Optional[bytes]:
		"""Get cached file content."""
		return self.file_cache.get(file_path)

	def _evict_cache_entries(self, needed_space: int):
		"""Evict cache entries to make space."""
		# Simple LRU eviction - remove oldest entries
		while self.current_cache_size + needed_space > self.max_cache_size and self.file_cache:
			oldest_key = next(iter(self.file_cache))
			content = self.file_cache.pop(oldest_key)
			self.current_cache_size -= len(content)

	def clear_cache(self):
		"""Clear all cached file content."""
		self.file_cache.clear()
		self.current_cache_size = 0
		logger.info("File cache cleared")

	def cleanup(self):
		"""Clean up all file resources."""
		# Close all open files
		for file_path in list(self.open_files.keys()):
			self.close_file(file_path)

		# Clear cache
		self.clear_cache()

		logger.info("File memory manager cleaned up")


# Global memory manager instance
memory_manager = MemoryManager()
file_memory_manager = FileMemoryManager(memory_manager)


def get_memory_manager() -> MemoryManager:
	"""Get the global memory manager instance."""
	return memory_manager


def get_file_memory_manager() -> FileMemoryManager:
	"""Get the global file memory manager instance."""
	return file_memory_manager


@contextmanager
def memory_context(operation_name: str):
	"""Context manager for memory-aware operations."""
	with MemoryContext(memory_manager, operation_name):
		yield


def track_memory_usage(func):
	"""Decorator to track memory usage of functions."""

	def wrapper(*args, **kwargs):
		with memory_context(f"function_{func.__name__}"):
			return func(*args, **kwargs)

	return wrapper


def cleanup_on_exit():
	"""Cleanup function to be called on application exit."""
	logger.info("Performing final memory cleanup")
	memory_manager.force_cleanup()
	file_memory_manager.cleanup()
	memory_manager.stop_monitoring()
