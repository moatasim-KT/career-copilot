"""
Database Initialization Script
Initializes all tables using SQLAlchemy models, adds indexes, and verifies foreign key constraints.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text
from app.core.database import engine, Base, SessionLocal
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

logger = get_logger(__name__)
settings = get_settings()


def check_existing_tables():
    """Check if tables already exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if existing_tables:
        logger.info(f"Found existing tables: {', '.join(existing_tables)}")
        return True
    return False


def create_tables():
    """Create all tables from SQLAlchemy models"""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


def verify_indexes():
    """Verify that all required indexes exist"""
    logger.info("Verifying indexes...")
    
    inspector = inspect(engine)
    
    # Expected indexes for each table
    expected_indexes = {
        'users': ['username', 'email'],
        'jobs': ['user_id', 'company', 'title', 'status', 'created_at'],
        'applications': ['user_id', 'job_id', 'status', 'created_at']
    }
    
    all_indexes_valid = True
    
    for table_name, expected_cols in expected_indexes.items():
        indexes = inspector.get_indexes(table_name)
        indexed_columns = set()
        
        for idx in indexes:
            indexed_columns.update(idx['column_names'])
        
        # Check primary key columns (they are automatically indexed)
        pk_constraint = inspector.get_pk_constraint(table_name)
        if pk_constraint:
            indexed_columns.update(pk_constraint['constrained_columns'])
        
        missing_indexes = []
        for col in expected_cols:
            if col not in indexed_columns:
                missing_indexes.append(col)
        
        if missing_indexes:
            logger.warning(f"⚠️  Table '{table_name}' missing indexes on: {', '.join(missing_indexes)}")
            all_indexes_valid = False
        else:
            logger.info(f"✅ Table '{table_name}' has all required indexes")
    
    return all_indexes_valid


def verify_foreign_keys():
    """Verify foreign key constraints"""
    logger.info("Verifying foreign key constraints...")
    
    inspector = inspect(engine)
    
    # Expected foreign keys
    expected_fks = {
        'jobs': [('user_id', 'users', 'id')],
        'applications': [
            ('user_id', 'users', 'id'),
            ('job_id', 'jobs', 'id')
        ]
    }
    
    all_fks_valid = True
    
    for table_name, expected in expected_fks.items():
        fks = inspector.get_foreign_keys(table_name)
        
        for local_col, ref_table, ref_col in expected:
            fk_found = False
            for fk in fks:
                if (local_col in fk['constrained_columns'] and 
                    fk['referred_table'] == ref_table and 
                    ref_col in fk['referred_columns']):
                    fk_found = True
                    break
            
            if fk_found:
                logger.info(f"✅ Foreign key: {table_name}.{local_col} -> {ref_table}.{ref_col}")
            else:
                logger.warning(f"⚠️  Missing foreign key: {table_name}.{local_col} -> {ref_table}.{ref_col}")
                all_fks_valid = False
    
    return all_fks_valid


def test_database_connection():
    """Test database connectivity"""
    logger.info("Testing database connection...")
    
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def get_table_info():
    """Display information about created tables"""
    logger.info("\n" + "="*60)
    logger.info("DATABASE SCHEMA INFORMATION")
    logger.info("="*60)
    
    inspector = inspect(engine)
    
    for table_name in inspector.get_table_names():
        logger.info(f"\nTable: {table_name}")
        logger.info("-" * 40)
        
        # Columns
        columns = inspector.get_columns(table_name)
        logger.info("Columns:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            col_type = str(col['type'])
            default = f" DEFAULT {col.get('default', 'None')}" if col.get('default') else ""
            logger.info(f"  - {col['name']}: {col_type} {nullable}{default}")
        
        # Indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            logger.info("Indexes:")
            for idx in indexes:
                unique = "UNIQUE" if idx['unique'] else ""
                logger.info(f"  - {idx['name']}: {', '.join(idx['column_names'])} {unique}")
        
        # Foreign Keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            logger.info("Foreign Keys:")
            for fk in fks:
                logger.info(f"  - {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
    
    logger.info("\n" + "="*60)


def main():
    """Main initialization function"""
    logger.info("="*60)
    logger.info("DATABASE INITIALIZATION SCRIPT")
    logger.info("="*60)
    logger.info(f"Database URL: {settings.database_url}")
    logger.info("")
    
    # Test connection
    if not test_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Check for existing tables
    existing = check_existing_tables()
    if existing:
        response = input("\n⚠️  Tables already exist. Recreate them? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Skipping table creation")
        else:
            logger.info("Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ Existing tables dropped")
            existing = False
    
    # Create tables if needed
    if not existing:
        if not create_tables():
            logger.error("❌ Database initialization failed")
            sys.exit(1)
    
    # Verify indexes
    logger.info("")
    verify_indexes()
    
    # Verify foreign keys
    logger.info("")
    verify_foreign_keys()
    
    # Display schema info
    logger.info("")
    get_table_info()
    
    logger.info("\n" + "="*60)
    logger.info("✅ DATABASE INITIALIZATION COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
