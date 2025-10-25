#!/usr/bin/env python3
"""
Script to initialize and seed the vector database with legal precedents.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set PYTHONPATH to include backend directory
os.environ['PYTHONPATH'] = str(backend_dir)

from app.core.config import get_config_value as get_config, get_config_value as get_backend_config
from app.core.logging import get_logger
from app.services.precedent_seeder import get_precedent_seeder_service
from app.services.vector_store_service import get_vector_store_service

logger = get_logger(__name__)


def main():
    """Main function to initialize and seed vector database."""
    parser = argparse.ArgumentParser(description="Initialize and seed vector database")
    parser.add_argument(
        "--force-reseed",
        action="store_true",
        help="Force reseed even if database already contains data"
    )
    parser.add_argument(
        "--export-file",
        type=str,
        help="Export precedents to JSON file after seeding"
    )
    parser.add_argument(
        "--import-file",
        type=str,
        help="Import precedents from JSON file instead of using built-in samples"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show database statistics without seeding"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check on vector database"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize services
        logger.info("Initializing vector database services...")
        vector_store = get_vector_store_service()
        seeder_service = get_precedent_seeder_service()
        
        # Health check
        if args.health_check:
            logger.info("Performing health check...")
            health = vector_store.health_check()
            print(f"Health Status: {health}")
            
            if health.get("status") != "healthy":
                logger.error("Vector database is not healthy!")
                return 1
        
        # Show current stats
        logger.info("Getting current database statistics...")
        initial_stats = vector_store.get_collection_stats()
        print(f"Current Database Stats: {initial_stats}")
        
        if args.stats_only:
            return 0
        
        # Import from file if specified
        if args.import_file:
            logger.info(f"Importing precedents from {args.import_file}...")
            import_result = seeder_service.import_precedents_from_json(args.import_file)
            print(f"Import Result: {import_result}")
            
            if import_result["status"] != "completed":
                logger.error("Import failed!")
                return 1
        
        # Seed with built-in samples
        else:
            logger.info("Seeding database with sample precedents...")
            seed_result = seeder_service.seed_precedents(force_reseed=args.force_reseed)
            print(f"Seed Result: {seed_result}")
            
            if seed_result["status"] == "failed":
                logger.error("Seeding failed!")
                return 1
        
    except Exception as e:
        logger.error(f"Error initializing or seeding vector database: {e}")
        return 1
    
    print("\n\u2705 Vector database initialization and seeding complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
