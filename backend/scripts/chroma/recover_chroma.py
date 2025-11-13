#!/usr/bin/env python3
"""
Safe ChromaDB recovery script.

- Backs up existing Chroma persist directory to <dir>.corrupted.<timestamp>
- Creates a fresh persist directory
- Attempts to initialize chromadb.PersistentClient with persistent settings
- Creates a small test collection to verify the client

Run from repo root with PYTHONPATH='.' so project settings are available.
"""

import logging
import os
import shutil
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recover_chroma")


def main():
	try:
		# Import settings from the project
		from backend.app.core.config import get_settings
	except Exception:
		# fallback to app.core.config path used in runtime
		from app.core.config import get_settings

	settings = get_settings()
	persist_dir = os.path.abspath(getattr(settings, "chroma_persist_directory", "data/chroma"))

	logger.info(f"Chroma persist directory: {persist_dir}")

	if not os.path.exists(persist_dir):
		logger.info("Persist directory does not exist; creating fresh directory")
		os.makedirs(persist_dir, exist_ok=True)

	# Backup existing directory
	timestamp = int(time.time())
	backup_dir = f"{persist_dir}.corrupted.{timestamp}"
	try:
		# Only move if directory appears to have content (more than .gitkeep etc)
		entries = [p for p in Path(persist_dir).iterdir() if p.name not in {".gitkeep", ".DS_Store"}]
		if entries:
			logger.info(f"Backing up existing persist directory to: {backup_dir}")
			shutil.move(persist_dir, backup_dir)
			os.makedirs(persist_dir, exist_ok=True)
		else:
			logger.info("Persist directory empty — no backup needed")
	except Exception as e:
		logger.error(f"Failed to backup persist directory: {e}")
		logger.exception(e)
		return 2

	# Attempt to initialize Chroma PersistentClient
	try:
		import chromadb
		from chromadb.config import Settings as ChromaSettings

		logger.info("Attempting to initialize chromadb.PersistentClient (fresh directory)")
		client = chromadb.PersistentClient(
			path=persist_dir, settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True, is_persistent=True)
		)

		# Try to list collections and create a test collection
		try:
			collections = client.list_collections()
			logger.info(f"Collections after initialization: {collections}")
		except Exception as e:
			logger.warning(f"Could not list collections immediately: {e}")

		test_collection_name = f"recovery_test_{timestamp}"
		try:
			client.get_or_create_collection(name=test_collection_name)
			logger.info(f"Created test collection: {test_collection_name}")
		except Exception as e:
			logger.error(f"Failed to create test collection: {e}")
			logger.exception(e)
			# Continue — initialization may still be partially successful

		# Close client if possible
		try:
			client.close()
		except Exception:
			pass

		logger.info("Chroma PersistentClient initialization completed — please inspect logs for any Rust panics.")
		logger.info(
			"If initialization succeeded, consider migrating data from the backup into the fresh store using application-level export/import or a dedicated conversion tool."
		)
		return 0

	except Exception as e:
		logger.error(f"Chroma initialization failed: {e}")
		logger.exception(e)
		logger.error(f"Persist directory backed up to: {backup_dir}")
		return 3


if __name__ == "__main__":
	import sys

	exit_code = main()
	sys.exit(exit_code)
