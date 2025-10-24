#!/usr/bin/env python3
"""
Database Initialization Script for Career Copilot.

This script handles complete database initialization including:
1. Creating database tables and indexes
2. Running migrations if needed
3. Seeding with sample data for development
4. Validating database health
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for local development
os.environ.setdefault("DEPLOYMENT_MODE", "development")
os.environ.setdefault("ENVIRONMENT", "development")

from app.core.database import get_database_manager, Base
from app.core.config_manager import initialize_configuration
from app.core.logging import get_logger
from app.models.database_models import User, ContractAnalysis, AuditLog
from app.services.database_seeder import get_database_seeder
from app.services.precedent_seeder import get_precedent_seeder_service

logger = get_logger(__name__)


async def create_database_tables() -> bool:
    """Create all database tables and indexes."""
    try:
        logger.info("Creating database tables...")
        
        # Get database manager
        db_manager = await get_database_manager()
        
        if db_manager.engine is None:
            logger.error("Database engine is None - configuration issue")
            return False
        
        # Create all tables
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("\u2705 Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"\u274c Error creating database tables: {e}")
        return False


async def seed_sample_data() -> bool:
    """Seed database with sample data for development."""
    try:
        logger.info("Seeding database with sample data...")
        
        # Seed vector database with precedent clauses
        precedent_seeder = get_precedent_seeder_service()
        precedent_result = precedent_seeder.seed_precedents(force_reseed=False)
        
        if precedent_result["status"] == "completed":
            logger.info(f"\u2705 Seeded {precedent_result['added_count']} precedent clauses")
        elif precedent_result["status"] == "skipped":
            logger.info(f"\u2139\ufe0f  Precedent seeding skipped: {precedent_result['message']}")
        else:
            logger.warning(f"\u26a0\ufe0f  Precedent seeding failed: {precedent_result.get('error', 'Unknown error')}")
        
        # Seed relational database with sample users (for development only)
        if os.getenv("ENVIRONMENT") == "development":
            await seed_development_users()
        
        logger.info("\u2705 Sample data seeding completed")
        return True
        
    except Exception as e:
        logger.error(f"\u274c Error seeding sample data: {e}")
        return False


async def seed_development_users() -> None:
    """Seed development users for testing."""
    try:
        from app.core.database import get_db_session
        from app.models.database_models import User, UserSettings
        import uuid
        import bcrypt
        
        async with get_db_session() as session:
            # Check if users already exist using raw SQL to handle schema differences
            from sqlalchemy import text
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
    # ... (rest of the file remains unchanged)
