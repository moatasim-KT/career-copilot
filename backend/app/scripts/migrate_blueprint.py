"""Migration script for blueprint improvements"""

from sqlalchemy import text
from ..core.database import engine, SessionLocal


def migrate():
    """Apply database migrations for blueprint features"""
    
    with engine.connect() as conn:
        # Add new columns to users table
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN skills JSON"))
            print("✅ Added skills column to users")
        except Exception as e:
            print(f"⚠️  skills column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_locations JSON"))
            print("✅ Added preferred_locations column to users")
        except Exception as e:
            print(f"⚠️  preferred_locations column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN experience_level VARCHAR"))
            print("✅ Added experience_level column to users")
        except Exception as e:
            print(f"⚠️  experience_level column may already exist: {e}")
        
        # Add new columns to jobs table
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN responsibilities TEXT"))
            print("✅ Added responsibilities column to jobs")
        except Exception as e:
            print(f"⚠️  responsibilities column may already exist: {e}")
        
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN date_applied TIMESTAMP"))
            print("✅ Added date_applied column to jobs")
        except Exception as e:
            print(f"⚠️  date_applied column may already exist: {e}")
        
        # Update source column default
        try:
            conn.execute(text("UPDATE jobs SET source = 'manual' WHERE source IS NULL"))
            print("✅ Updated source column defaults")
        except Exception as e:
            print(f"⚠️  Error updating source defaults: {e}")
        
        conn.commit()
    
    print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    migrate()
