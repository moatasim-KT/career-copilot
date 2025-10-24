"""Reset database - drop all tables and recreate"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import Base, engine
from app.models.user import User
from app.models.job import Job
from app.models.application import Application


def reset_database():
    """Drop and recreate all tables"""
    print("Resetting database...")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("\u2713 Dropped all tables")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("\u2713 Created all tables")
        
        print("\nDatabase reset complete!")
        
    except Exception as e:
        print(f"\u2717 Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    response = input("This will delete all data. Continue? (yes/no): ")
    if response.lower() == "yes":
        reset_database()
    else:
        print("Cancelled.")
