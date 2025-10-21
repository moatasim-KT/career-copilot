"""
Database initialization utilities
"""

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models import Base


def create_database_extensions():
    """Create PostgreSQL extensions required by the application"""
    with engine.connect() as connection:
        # Enable UUID extension for generating UUIDs
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        
        # Enable trigram extension for fuzzy text search
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
        
        # Set timezone to UTC
        connection.execute(text("SET timezone = 'UTC'"))
        
        connection.commit()


def create_all_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def init_database():
    """Initialize the database with extensions and tables"""
    try:
        # Create extensions first
        create_database_extensions()
        print("✓ Database extensions created successfully")
        
        # Create all tables
        create_all_tables()
        print("✓ Database tables created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def check_database_connection():
    """Check if database connection is working"""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Initializing Career Co-Pilot database...")
    
    if check_database_connection():
        if init_database():
            print("🎉 Database initialization completed successfully!")
        else:
            print("❌ Database initialization failed!")
    else:
        print("❌ Cannot connect to database!")