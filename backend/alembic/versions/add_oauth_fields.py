"""
Migration to add OAuth fields to users table
"""

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add OAuth fields to users table"""
    with engine.connect() as conn:
        # Add OAuth columns
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN oauth_provider TEXT
            """))
        except Exception as e:
            print(f"oauth_provider column might already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN oauth_id TEXT
            """))
        except Exception as e:
            print(f"oauth_id column might already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN profile_picture_url TEXT
            """))
        except Exception as e:
            print(f"profile_picture_url column might already exist: {e}")
        
        conn.commit()
        print("✅ Added OAuth fields to users table")


def downgrade():
    """Remove OAuth fields from users table"""
    with engine.connect() as conn:
        # SQLite doesn't support DROP COLUMN, so we'd need to recreate the table
        # For now, just print a message
        print("⚠️ SQLite doesn't support DROP COLUMN - OAuth fields will remain")


if __name__ == "__main__":
    upgrade()