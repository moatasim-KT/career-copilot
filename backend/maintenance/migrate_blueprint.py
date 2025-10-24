"""Migration script for blueprint improvements"""

from sqlalchemy import text
from ..core.database import engine, SessionLocal


def migrate():
    """Apply database migrations for blueprint features"""
    
    with engine.connect() as conn:
        # Add new columns to users table
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN skills JSON"))
            print("\u2705 Added skills column to users")
        except Exception as e:
            print(f"\u26a0\ufe0f  skills column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_locations JSON"))
            print("\u2705 Added preferred_locations column to users")
        except Exception as e:
            print(f"\u26a0\ufe0f  preferred_locations column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN experience_level VARCHAR"))
            print("\u2705 Added experience_level column to users")
        except Exception as e:
            print(f"\u26a0\ufe0f  experience_level column may already exist: {e}")
        
        # Add new columns to jobs table
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN responsibilities TEXT"))
            print("\u2705 Added responsibilities column to jobs")
        except Exception as e:
            print(f"\u26a0\ufe0f  responsibilities column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN date_applied TIMESTAMP"))
            print("\u2705 Added date_applied column to jobs")
        except Exception as e:
            print(f"\u26a0\ufe0f  date_applied column may already exist: {e}")
        
        # Update source column default
        try:
            conn.execute(text("UPDATE jobs SET source = 'manual' WHERE source IS NULL"))
            print("\u2705 Updated source column defaults")
        except Exception as e:
            print(f"\u26a0\ufe0f  Error updating source defaults: {e}")
        
        conn.commit()
    
    print("\n\u2705 Migration completed successfully!")


if __name__ == "__main__":
    migrate()
