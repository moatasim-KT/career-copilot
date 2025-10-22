#!/usr/bin/env python3
"""
Simple Database Initialization Script
Creates the database and tables without async issues
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import Base

def main():
    """Initialize database"""
    print("🚀 Initializing Career Copilot Database")
    print("=" * 50)
    
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)