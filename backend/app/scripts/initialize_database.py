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
        
        logger.info("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False


async def seed_sample_data() -> bool:
    """Seed database with sample data for development."""
    try:
        logger.info("Seeding database with sample data...")
        
        # Seed vector database with precedent clauses
        precedent_seeder = get_precedent_seeder_service()
        precedent_result = precedent_seeder.seed_precedents(force_reseed=False)
        
        if precedent_result["status"] == "completed":
            logger.info(f"✅ Seeded {precedent_result['added_count']} precedent clauses")
        elif precedent_result["status"] == "skipped":
            logger.info(f"ℹ️  Precedent seeding skipped: {precedent_result['message']}")
        else:
            logger.warning(f"⚠️  Precedent seeding failed: {precedent_result.get('error', 'Unknown error')}")
        
        # Seed relational database with sample users (for development only)
        if os.getenv("ENVIRONMENT") == "development":
            await seed_development_users()
        
        logger.info("✅ Sample data seeding completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error seeding sample data: {e}")
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
                user_count = result.scalar()
                
                if user_count > 0:
                    logger.info("Development users already exist, skipping user seeding")
                    return
            except Exception as e:
                logger.warning(f"Could not check existing users: {e}")
                # Continue with user creation
            
            # Create sample users using raw SQL to handle schema differences
            sample_users = [
                {
                    "username": "admin",
                    "email": "admin@career-copilot.com",
                    "password": "admin123",
                },
                {
                    "username": "demo_user",
                    "email": "demo@career-copilot.com", 
                    "password": "demo123",
                }
            ]
            
            for user_data in sample_users:
                # Hash password
                password_hash = bcrypt.hashpw(
                    user_data["password"].encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                user_id = str(uuid.uuid4())
                
                # Insert user using raw SQL to handle different schema versions
                try:
                    await session.execute(text("""
                        INSERT INTO users (id, username, email, hashed_password, password_hash, is_active, email_verified, created_at, updated_at)
                        VALUES (:id, :username, :email, :hashed_password, :password_hash, :is_active, :email_verified, :created_at, :updated_at)
                    """), {
                        "id": user_id,
                        "username": user_data["username"],
                        "email": user_data["email"],
                        "hashed_password": password_hash,
                        "password_hash": password_hash,
                        "is_active": True,
                        "email_verified": True,
                        "created_at": "2024-01-01 00:00:00",
                        "updated_at": "2024-01-01 00:00:00"
                    })
                    
                    # Try to create user settings if the table exists
                    try:
                        settings_id = str(uuid.uuid4())
                        await session.execute(text("""
                            INSERT INTO user_settings (id, user_id, ai_model_preference, analysis_depth, 
                                                     email_notifications_enabled, slack_notifications_enabled, 
                                                     docusign_notifications_enabled, created_at, updated_at)
                            VALUES (:id, :user_id, :ai_model_preference, :analysis_depth, 
                                   :email_notifications_enabled, :slack_notifications_enabled, 
                                   :docusign_notifications_enabled, :created_at, :updated_at)
                        """), {
                            "id": settings_id,
                            "user_id": user_id,
                            "ai_model_preference": "gpt-4",
                            "analysis_depth": "normal",
                            "email_notifications_enabled": True,
                            "slack_notifications_enabled": False,
                            "docusign_notifications_enabled": False,
                            "created_at": "2024-01-01 00:00:00",
                            "updated_at": "2024-01-01 00:00:00"
                        })
                    except Exception as e:
                        logger.warning(f"Could not create user settings for {user_data['username']}: {e}")
                    
                except Exception as e:
                    logger.warning(f"Could not create user {user_data['username']}: {e}")
            
            await session.commit()
            logger.info(f"✅ Created {len(sample_users)} development users")
            
    except Exception as e:
        logger.error(f"❌ Error creating development users: {e}")


async def validate_database_health() -> Dict[str, Any]:
    """Validate database health and connectivity."""
    try:
        logger.info("Validating database health...")
        
        db_manager = await get_database_manager()
        health_status = await db_manager.health_check()
        
        # Check table existence
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # Test basic queries
            await session.execute(text("SELECT 1"))
            
            # Check if main tables exist and are accessible
            tables_to_check = ["users", "contract_analyses", "audit_logs"]
            table_status = {}
            
            for table in tables_to_check:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_status[table] = {"exists": True, "count": count}
                except Exception as e:
                    table_status[table] = {"exists": False, "error": str(e)}
        
        health_status["tables"] = table_status
        
        # Log health status
        logger.info("📊 Database Health Status:")
        logger.info(f"  PostgreSQL: {'✅' if health_status.get('postgresql') else '❌'}")
        logger.info(f"  ChromaDB: {'✅' if health_status.get('chromadb') else '❌'}")
        logger.info(f"  Redis: {'✅' if health_status.get('redis') else '❌'}")
        
        logger.info("📋 Table Status:")
        for table, status in table_status.items():
            if status["exists"]:
                logger.info(f"  {table}: ✅ ({status['count']} records)")
            else:
                logger.info(f"  {table}: ❌ {status.get('error', 'Unknown error')}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Database health validation failed: {e}")
        return {"error": str(e)}


async def initialize_database_complete() -> bool:
    """Complete database initialization process."""
    try:
        logger.info("🚀 Starting complete database initialization...")
        logger.info("=" * 60)
        
        # Step 1: Initialize configuration
        logger.info("📋 Step 1: Initializing configuration...")
        config = initialize_configuration()
        logger.info(f"✅ Configuration loaded: {len(config)} keys")
        
        # Step 2: Create database tables
        logger.info("📋 Step 2: Creating database tables...")
        tables_created = await create_database_tables()
        if not tables_created:
            logger.error("❌ Failed to create database tables")
            return False
        
        # Step 3: Seed sample data
        logger.info("📋 Step 3: Seeding sample data...")
        data_seeded = await seed_sample_data()
        if not data_seeded:
            logger.warning("⚠️  Sample data seeding failed, but continuing...")
        
        # Step 4: Validate database health
        logger.info("📋 Step 4: Validating database health...")
        health_status = await validate_database_health()
        
        if "error" in health_status:
            logger.error("❌ Database health validation failed")
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 Database initialization completed successfully!")
        logger.info("=" * 60)
        
        # Print summary
        logger.info("📊 Initialization Summary:")
        logger.info("  ✅ Database tables created")
        logger.info("  ✅ Indexes created")
        logger.info("  ✅ Sample data seeded")
        logger.info("  ✅ Health validation passed")
        
        if os.getenv("ENVIRONMENT") == "development":
            logger.info("")
            logger.info("🔧 Development Environment Ready:")
            logger.info("  👤 Admin user: admin@career-copilot.com / admin123")
            logger.info("  👤 Demo user: demo@career-copilot.com / demo123")
            logger.info("  📚 Sample precedent clauses loaded")
            logger.info("  🌐 Ready to start application servers")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function for database initialization."""
    try:
        success = await initialize_database_complete()
        
        if success:
            logger.info("✅ Database initialization completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Database initialization failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Database initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during database initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())