"""
Memory management and temporary file cleanup.
"""

import gc
import logging
import os
import tempfile
import threading
import time
import weakref
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil


class MemoryManager:
	"""Advanced memory management and cleanup for security."""

	def __init__(self, max_memory_mb: int = 500, cleanup_interval: int = 300):
		self.logger = logging.getLogger(__name__)
		self.max_memory_mb = max_memory_mb
		self.cleanup_interval = cleanup_interval

		# Track file references
		self.temp_files: Dict[str, Dict[str, Any]] = {}
		self.file_refs: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

		# Memory monitoring
		self.memory_usage_history: List[float] = []
		self.max_history_size = 100

		# Process monitoring
		self.process = psutil.Process()

		# Start cleanup thread
		self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
		self.cleanup_thread.start()

	def register_temp_file(self, file_path: Path, file_size: int, created_by: str = "unknown", ttl_hours: int = 24) -> str:
		"""
		Register a temporary file for tracking and cleanup.

		Args:
		    file_path: Path to the temporary file
		    file_size: Size of the file in bytes
		    created_by: Identifier of who created the file
		    ttl_hours: Time to live in hours

		Returns:
		    File ID for tracking
		"""
		file_id = f"{int(time.time())}_{os.urandom(4).hex()}"

		self.temp_files[file_id] = {
			"path": str(file_path),
			"size": file_size,
			"created_at": datetime.utcnow(),
			"created_by": created_by,
			"ttl_hours": ttl_hours,
			"access_count": 0,
			"last_accessed": datetime.utcnow(),
			"is_secure": True,
		}

		self.logger.info(f"Registered temp file: {file_id} ({file_size} bytes)")
		return file_id

	def access_file(self, file_id: str) -> Optional[Path]:
		"""
		Access a registered temporary file.

		Args:
		    file_id: File ID to access

		Returns:
		    Path to the file if it exists and is accessible
		"""
		if file_id not in self.temp_files:
			return None

		file_info = self.temp_files[file_id]
		file_path = Path(file_info["path"])

		if not file_path.exists():
			self.logger.warning(f"Temp file not found: {file_id}")
			del self.temp_files[file_id]
			return None

		# Update access statistics
		file_info["access_count"] += 1
		file_info["last_accessed"] = datetime.utcnow()

		return file_path

	def secure_delete_file(self, file_id: str) -> bool:
		"""
		Securely delete a temporary file.

		Args:
		    file_id: File ID to delete

		Returns:
		    True if file was deleted successfully
		"""
		if file_id not in self.temp_files:
			return False

		file_info = self.temp_files[file_id]
		file_path = Path(file_info["path"])

		try:
			if file_path.exists():
				# Overwrite file with random data before deletion
				self._secure_overwrite_file(file_path)

				# Delete the file
				file_path.unlink()

				self.logger.info(f"Securely deleted temp file: {file_id}")

			# Remove from tracking
			del self.temp_files[file_id]
			return True

		except Exception as e:
			self.logger.error(f"Failed to securely delete file {file_id}: {e!s}")
			return False

	def _secure_overwrite_file(self, file_path: Path):
		"""Securely overwrite file with random data."""
		try:
			file_size = file_path.stat().st_size

			with open(file_path, "r+b") as f:
				# Write random data
				f.write(os.urandom(file_size))
				f.flush()
				os.fsync(f.fileno())

		except Exception as e:
			self.logger.error(f"Failed to overwrite file {file_path}: {e!s}")

	def cleanup_expired_files(self) -> int:
		"""
		Clean up expired temporary files.

		Returns:
		    Number of files cleaned up
		"""
		cleaned_count = 0
		current_time = datetime.utcnow()

		expired_files = []

		for file_id, file_info in self.temp_files.items():
			created_at = file_info["created_at"]
			ttl_hours = file_info["ttl_hours"]

			if current_time - created_at > timedelta(hours=ttl_hours):
				expired_files.append(file_id)

		for file_id in expired_files:
			if self.secure_delete_file(file_id):
				cleaned_count += 1

		if cleaned_count > 0:
			self.logger.info(f"Cleaned up {cleaned_count} expired temp files")

		return cleaned_count

	def get_memory_usage(self) -> Dict[str, Any]:
		"""Get current memory usage statistics."""
		memory_info = self.process.memory_info()

		return {
			"rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
			"vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
			"percent": self.process.memory_percent(),
			"available_mb": psutil.virtual_memory().available / 1024 / 1024,
			"total_mb": psutil.virtual_memory().total / 1024 / 1024,
		}

	def check_memory_limit(self) -> bool:
		"""Check if memory usage is within limits."""
		memory_usage = self.get_memory_usage()
		rss_mb = memory_usage["rss_mb"]

		# Add to history
		self.memory_usage_history.append(rss_mb)
		if len(self.memory_usage_history) > self.max_history_size:
			self.memory_usage_history.pop(0)

		return rss_mb <= self.max_memory_mb

	def force_cleanup(self) -> Dict[str, Any]:
		"""
		Force cleanup of memory and temporary files.

		Returns:
		    Cleanup statistics
		"""
		stats = {"files_cleaned": 0, "memory_freed_mb": 0, "gc_collections": 0}

		# Clean up expired files
		stats["files_cleaned"] = self.cleanup_expired_files()

		# Force garbage collection
		initial_memory = self.get_memory_usage()["rss_mb"]
		gc.collect()
		final_memory = self.get_memory_usage()["rss_mb"]
		stats["memory_freed_mb"] = initial_memory - final_memory
		stats["gc_collections"] = len(gc.garbage)

		self.logger.info(f"Force cleanup completed: {stats}")
		return stats

	def get_temp_file_stats(self) -> Dict[str, Any]:
		"""Get statistics about temporary files."""
		if not self.temp_files:
			return {"total_files": 0, "total_size_mb": 0, "oldest_file": None, "newest_file": None}

		total_size = sum(file_info["size"] for file_info in self.temp_files.values())
		created_times = [file_info["created_at"] for file_info in self.temp_files.values()]

		return {
			"total_files": len(self.temp_files),
			"total_size_mb": total_size / 1024 / 1024,
			"oldest_file": min(created_times).isoformat() if created_times else None,
			"newest_file": max(created_times).isoformat() if created_times else None,
			"files_by_creator": self._get_files_by_creator(),
		}

	def _get_files_by_creator(self) -> Dict[str, int]:
		"""Get file count by creator."""
		creator_counts = {}
		for file_info in self.temp_files.values():
			creator = file_info["created_by"]
			creator_counts[creator] = creator_counts.get(creator, 0) + 1
		return creator_counts

	def _cleanup_loop(self):
		"""Background cleanup loop."""
		while True:
			try:
				# Check memory usage
				if not self.check_memory_limit():
					self.logger.warning("Memory usage exceeded limit, forcing cleanup")
					self.force_cleanup()

				# Clean up expired files
				self.cleanup_expired_files()

				# Sleep for cleanup interval
				time.sleep(self.cleanup_interval)

			except Exception as e:
				self.logger.error(f"Cleanup loop error: {e!s}")
				time.sleep(60)  # Wait before retrying

	def create_secure_temp_file(self, content: bytes, suffix: str = ".tmp", created_by: str = "unknown") -> Optional[tuple[str, Path]]:
		"""
		Create a secure temporary file with automatic cleanup.

		Args:
		    content: File content
		    suffix: File suffix
		    created_by: Creator identifier

		Returns:
		    Tuple of (file_id, file_path) or None if failed
		"""
		try:
			# Create temporary file
			with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
				temp_file.write(content)
				temp_file.flush()
				os.fsync(temp_file.fileno())

				file_path = Path(temp_file.name)

				# Set restrictive permissions
				os.chmod(file_path, 0o600)

				# Register for cleanup
				file_id = self.register_temp_file(file_path, len(content), created_by)

				return file_id, file_path

		except Exception as e:
			self.logger.error(f"Failed to create secure temp file: {e!s}")
			return None

	def cleanup_all_files(self) -> int:
		"""Clean up all tracked temporary files."""
		file_ids = list(self.temp_files.keys())
		cleaned_count = 0

		for file_id in file_ids:
			if self.secure_delete_file(file_id):
				cleaned_count += 1

		self.logger.info(f"Cleaned up all {cleaned_count} temp files")
		return cleaned_count

	def get_memory_history(self) -> List[float]:
		"""Get memory usage history."""
		return self.memory_usage_history.copy()

	def set_memory_limit(self, max_memory_mb: int):
		"""Set new memory limit."""
		self.max_memory_mb = max_memory_mb
		self.logger.info(f"Memory limit set to {max_memory_mb}MB")

	def __del__(self):
		"""Cleanup on destruction."""
		try:
			self.cleanup_all_files()
		except Exception:
			pass  # Ignore errors during cleanup
