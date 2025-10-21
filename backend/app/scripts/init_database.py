"""Initialize database with tables"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import Base, engine, init_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application


def main():
    """Create all database tables"""
    print("Creating database tables...")
    
    try:
        init_db()
        print("✓ Database tables created successfully!")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nCreated tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
