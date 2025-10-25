#!/usr/bin/env python3
"""
Database seeding script for the Career Copilot application.

This script can be used to seed the ChromaDB vector store with sample
precedent clauses for development and testing purposes.
"""

import argparse
import logging
import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_config_value as get_config, get_config_value as get_backend_config
from app.core.logging import setup_logging
from app.services.database_seeder import get_database_seeder
from app.services.vector_store import get_vector_store_service


def main():
	"""Main function for the database seeding script."""
	parser = argparse.ArgumentParser(description="Seed the vector database with precedent clauses")
	parser.add_argument("--reset", action="store_true", help="Reset the existing collection before seeding")
	parser.add_argument("--stats-only", action="store_true", help="Only show database statistics without seeding")
	parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level")

	args = parser.parse_args()

	# Setup logging
	setup_logging(log_level=args.log_level)
	logger = logging.getLogger(__name__)

	try:
		# Validate configuration
		logger.info("Validating configuration...")
		validate_required_settings()

		# Initialize services
		logger.info("Initializing vector store service...")
		vector_store = get_vector_store_service()

		# Show current statistics
		logger.info("Getting current database statistics...")
		stats = vector_store.get_collection_stats()
		logger.info(f"Current database stats:")
		logger.info(f"  Total clauses: {stats['total_clauses']}")
		logger.info(f"  Categories: {stats['categories']}")
		logger.info(f"  Risk levels: {stats['risk_levels']}")

		if args.stats_only:
			logger.info("Stats-only mode. Exiting.")
			return

		# Initialize seeder
		logger.info("Initializing database seeder...")
		seeder = get_database_seeder(vector_store)

		# Perform seeding
		logger.info("Starting database seeding...")
		seeder.seed_database(reset_existing=args.reset)

		# Show final statistics
		final_stats = vector_store.get_collection_stats()
		logger.info(f"Final database stats:")
		logger.info(f"  Total clauses: {final_stats['total_clauses']}")
		logger.info(f"  Categories: {final_stats['categories']}")
		logger.info(f"  Risk levels: {final_stats['risk_levels']}")

		logger.info("Database seeding completed successfully!")

	except Exception as e:
		logger.error(f"Database seeding failed: {e!s}")
		sys.exit(1)


if __name__ == "__main__":
	main()
