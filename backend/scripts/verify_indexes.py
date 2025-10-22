#!/usr/bin/env python3
"""
Script to verify database indexes and test query performance.
This script checks that all required indexes are in place and tests query performance.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import User, Job, Application
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_indexes():
    """Verify that all required indexes are in place and test query performance."""
    
    # Get database URL
    settings = get_settings()
    database_url = settings.database_url
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        logger.info("=== Database Index Verification ===")
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = "sqlite" in database_url.lower()
        
        if is_sqlite:
            # SQLite index verification
            logger.info("Database: SQLite")
            verify_sqlite_indexes(session)
        else:
            # PostgreSQL index verification
            logger.info("Database: PostgreSQL")
            verify_postgresql_indexes(session)
        
        # Test query performance with sample data
        test_query_performance(session, is_sqlite)

def verify_sqlite_indexes(session):
    """Verify indexes in SQLite database."""
    
    # Get all indexes
    result = session.execute(text("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"))
    indexes = result.fetchall()
    
    logger.info("\n--- SQLite Indexes ---")
    for index in indexes:
        logger.info(f"Index: {index[0]} on table {index[1]}")
        logger.info(f"SQL: {index[2]}")
    
    # Check for required indexes
    required_indexes = {
        'users': ['username', 'email'],
        'jobs': ['user_id', 'company', 'title', 'created_at'],
        'applications': ['user_id', 'job_id', 'status']
    }
    
    for table, columns in required_indexes.items():
        logger.info(f"\n--- Checking {table} table indexes ---")
        for column in columns:
            # Check if index exists for this column
            index_found = any(column in str(index[2]).lower() for index in indexes if index[1] == table)
            status = "✅ FOUND" if index_found else "❌ MISSING"
            logger.info(f"{column}: {status}")

def verify_postgresql_indexes(session):
    """Verify indexes in PostgreSQL database."""
    
    # Get all indexes
    query = text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)
    
    result = session.execute(query)
    indexes = result.fetchall()
    
    logger.info("\n--- PostgreSQL Indexes ---")
    for index in indexes:
        logger.info(f"Table: {index[1]}, Index: {index[2]}")
        logger.info(f"Definition: {index[3]}")
    
    # Check for required indexes
    required_indexes = {
        'users': ['username', 'email'],
        'jobs': ['user_id', 'company', 'title', 'created_at'],
        'applications': ['user_id', 'job_id', 'status']
    }
    
    for table, columns in required_indexes.items():
        logger.info(f"\n--- Checking {table} table indexes ---")
        for column in columns:
            # Check if index exists for this column
            index_found = any(column in str(index[3]).lower() for index in indexes if index[1] == table)
            status = "✅ FOUND" if index_found else "❌ MISSING"
            logger.info(f"{column}: {status}")

def test_query_performance(session, is_sqlite):
    """Test query performance using EXPLAIN."""
    
    logger.info("\n=== Query Performance Testing ===")
    
    # Test queries that should use indexes
    test_queries = [
        # User queries
        ("SELECT * FROM users WHERE username = 'testuser'", "User lookup by username"),
        ("SELECT * FROM users WHERE email = 'test@example.com'", "User lookup by email"),
        
        # Job queries
        ("SELECT * FROM jobs WHERE user_id = 1", "Jobs by user_id"),
        ("SELECT * FROM jobs WHERE company = 'Google'", "Jobs by company"),
        ("SELECT * FROM jobs WHERE title LIKE '%Engineer%'", "Jobs by title pattern"),
        ("SELECT * FROM jobs WHERE user_id = 1 ORDER BY created_at DESC", "Recent jobs by user"),
        
        # Application queries
        ("SELECT * FROM applications WHERE user_id = 1", "Applications by user_id"),
        ("SELECT * FROM applications WHERE job_id = 1", "Applications by job_id"),
        ("SELECT * FROM applications WHERE status = 'applied'", "Applications by status"),
        ("SELECT * FROM applications WHERE user_id = 1 AND status = 'interview'", "User applications by status"),
        
        # Complex queries
        ("""
        SELECT j.*, a.status 
        FROM jobs j 
        LEFT JOIN applications a ON j.id = a.job_id 
        WHERE j.user_id = 1 
        ORDER BY j.created_at DESC
        """, "Jobs with application status"),
        
        ("""
        SELECT COUNT(*) 
        FROM applications 
        WHERE user_id = 1 AND status IN ('applied', 'interview', 'offer')
        """, "Active applications count")
    ]
    
    for query, description in test_queries:
        logger.info(f"\n--- {description} ---")
        logger.info(f"Query: {query.strip()}")
        
        try:
            if is_sqlite:
                explain_query = f"EXPLAIN QUERY PLAN {query}"
            else:
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS) {query}"
            
            result = session.execute(text(explain_query))
            
            logger.info("Execution Plan:")
            for row in result:
                logger.info(f"  {row}")
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")

def create_sample_data_for_testing(session):
    """Create some sample data to test queries against."""
    
    logger.info("\n=== Creating Sample Data for Testing ===")
    
    try:
        # Check if we already have data
        user_count = session.query(User).count()
        if user_count > 0:
            logger.info(f"Found {user_count} existing users, skipping sample data creation")
            return
        
        # Create sample user
        from app.security.password import get_password_hash
        
        sample_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            skills=["Python", "FastAPI", "SQLAlchemy"],
            preferred_locations=["San Francisco", "Remote"],
            experience_level="mid"
        )
        session.add(sample_user)
        session.flush()  # Get the user ID
        
        # Create sample jobs
        sample_jobs = [
            Job(
                user_id=sample_user.id,
                company="Google",
                title="Software Engineer",
                location="San Francisco",
                tech_stack=["Python", "Go", "Kubernetes"],
                source="manual"
            ),
            Job(
                user_id=sample_user.id,
                company="Meta",
                title="Backend Engineer",
                location="Menlo Park",
                tech_stack=["Python", "React", "GraphQL"],
                source="scraped"
            ),
            Job(
                user_id=sample_user.id,
                company="Netflix",
                title="Senior Software Engineer",
                location="Los Gatos",
                tech_stack=["Java", "Python", "Microservices"],
                source="manual"
            )
        ]
        
        for job in sample_jobs:
            session.add(job)
        
        session.flush()  # Get job IDs
        
        # Create sample applications
        sample_applications = [
            Application(
                user_id=sample_user.id,
                job_id=sample_jobs[0].id,
                status="applied"
            ),
            Application(
                user_id=sample_user.id,
                job_id=sample_jobs[1].id,
                status="interview"
            )
        ]
        
        for app in sample_applications:
            session.add(app)
        
        session.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample data: {e}")

if __name__ == "__main__":
    try:
        verify_indexes()
        logger.info("\n=== Index verification completed ===")
    except Exception as e:
        logger.error(f"Error during index verification: {e}")
        sys.exit(1)