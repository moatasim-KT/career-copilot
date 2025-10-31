"""
Compression service for file and data compression
"""

import gzip
import zlib
import bz2
import lzma
from typing import Tuple, Optional
from enum import Enum
import json

from app.core.config import settings


class CompressionType(Enum):
	"""Supported compression types"""

	GZIP = "gzip"
	ZLIB = "zlib"
	BZ2 = "bz2"
	LZMA = "lzma"
	NONE = "none"


class CompressionService:
	"""Service for compressing and decompressing data and files"""

	def __init__(self):
		# Default compression settings
		self.default_compression_type = CompressionType.GZIP
		self.compression_level = getattr(settings, "COMPRESSION_LEVEL", 6)  # 1-9, 6 is good balance
		self.min_file_size_for_compression = getattr(settings, "MIN_COMPRESSION_SIZE", 1024)  # 1KB

	def should_compress(self, data_size: int, mime_type: Optional[str] = None) -> bool:
		"""Determine if data should be compressed based on size and type"""

		# Don't compress small files
		if data_size < self.min_file_size_for_compression:
			return False

		# Don't compress already compressed formats
		if mime_type:
			compressed_types = {
				"image/jpeg",
				"image/png",
				"image/gif",
				"image/webp",
				"video/mp4",
				"video/avi",
				"video/mov",
				"audio/mp3",
				"audio/wav",
				"audio/ogg",
				"application/zip",
				"application/rar",
				"application/7z",
				"application/gzip",
				"application/x-bzip2",
			}
			if mime_type.lower() in compressed_types:
				return False

		return True

	def compress_data(self, data: bytes, compression_type: CompressionType = None) -> Tuple[bytes, CompressionType]:
		"""Compress data using specified compression algorithm"""

		if not data:
			return data, CompressionType.NONE

		if compression_type is None:
			compression_type = self.default_compression_type

		try:
			if compression_type == CompressionType.GZIP:
				compressed_data = gzip.compress(data, compresslevel=self.compression_level)
			elif compression_type == CompressionType.ZLIB:
				compressed_data = zlib.compress(data, level=self.compression_level)
			elif compression_type == CompressionType.BZ2:
				compressed_data = bz2.compress(data, compresslevel=self.compression_level)
			elif compression_type == CompressionType.LZMA:
				compressed_data = lzma.compress(data, preset=self.compression_level)
			else:
				return data, CompressionType.NONE

			# Only return compressed data if it's actually smaller
			if len(compressed_data) < len(data):
				return compressed_data, compression_type
			else:
				return data, CompressionType.NONE

		except Exception as e:
			# If compression fails, return original data
			print(f"Compression failed: {e!s}")
			return data, CompressionType.NONE

	def decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
		"""Decompress data using specified compression algorithm"""

		if not data or compression_type == CompressionType.NONE:
			return data

		try:
			if compression_type == CompressionType.GZIP:
				return gzip.decompress(data)
			elif compression_type == CompressionType.ZLIB:
				return zlib.decompress(data)
			elif compression_type == CompressionType.BZ2:
				return bz2.decompress(data)
			elif compression_type == CompressionType.LZMA:
				return lzma.decompress(data)
			else:
				return data

		except Exception as e:
			raise ValueError(f"Decompression failed: {e!s}")

	def compress_text(self, text: str, compression_type: CompressionType = None) -> Tuple[bytes, CompressionType]:
		"""Compress text data"""
		if not text:
			return b"", CompressionType.NONE

		return self.compress_data(text.encode("utf-8"), compression_type)

	def decompress_text(self, data: bytes, compression_type: CompressionType) -> str:
		"""Decompress text data"""
		if not data:
			return ""

		decompressed_data = self.decompress_data(data, compression_type)
		return decompressed_data.decode("utf-8")

	def compress_json(self, json_data: dict, compression_type: CompressionType = None) -> Tuple[bytes, CompressionType]:
		"""Compress JSON data"""
		if not json_data:
			return b"", CompressionType.NONE

		json_string = json.dumps(json_data, separators=(",", ":"))  # Compact JSON
		return self.compress_text(json_string, compression_type)

	def decompress_json(self, data: bytes, compression_type: CompressionType) -> dict:
		"""Decompress JSON data"""
		if not data:
			return {}

		json_string = self.decompress_text(data, compression_type)
		return json.loads(json_string)

	def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
		"""Calculate compression ratio"""
		if original_size == 0:
			return 0.0
		return (original_size - compressed_size) / original_size

	def get_compression_stats(self, original_data: bytes, compressed_data: bytes, compression_type: CompressionType) -> dict:
		"""Get detailed compression statistics"""

		original_size = len(original_data)
		compressed_size = len(compressed_data)
		ratio = self.get_compression_ratio(original_size, compressed_size)

		return {
			"original_size": original_size,
			"compressed_size": compressed_size,
			"compression_ratio": ratio,
			"space_saved_bytes": original_size - compressed_size,
			"space_saved_percent": ratio * 100,
			"compression_type": compression_type.value,
		}

	def find_best_compression(self, data: bytes) -> Tuple[bytes, CompressionType, dict]:
		"""Find the best compression algorithm for given data"""

		if not data or len(data) < self.min_file_size_for_compression:
			return data, CompressionType.NONE, {}

		best_compressed = data
		best_type = CompressionType.NONE
		best_stats = {}

		# Try different compression algorithms
		algorithms = [CompressionType.GZIP, CompressionType.ZLIB, CompressionType.BZ2, CompressionType.LZMA]

		for algorithm in algorithms:
			try:
				compressed_data, compression_type = self.compress_data(data, algorithm)

				if len(compressed_data) < len(best_compressed):
					best_compressed = compressed_data
					best_type = compression_type
					best_stats = self.get_compression_stats(data, compressed_data, compression_type)

			except Exception:
				continue

		return best_compressed, best_type, best_stats

	def compress_file_content(
		self, file_data: bytes, mime_type: Optional[str] = None, auto_select: bool = True
	) -> Tuple[bytes, CompressionType, dict]:
		"""Compress file content with optional automatic algorithm selection"""

		if not self.should_compress(len(file_data), mime_type):
			return file_data, CompressionType.NONE, {}

		if auto_select:
			return self.find_best_compression(file_data)
		else:
			compressed_data, compression_type = self.compress_data(file_data)
			stats = self.get_compression_stats(file_data, compressed_data, compression_type)
			return compressed_data, compression_type, stats


# Global compression service instance
compression_service = CompressionService()
