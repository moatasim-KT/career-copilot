"""
Migration to add is_admin field to users table
"""

from sqlalchemy import text
from app.core.database import engine


def upgrade():
    """Add is_admin field to users table"""
    with engine.connect() as conn:
        # Add is_admin column with default False
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL
        """))
        
        # Make the first user (id=1) an admin if they exist
        conn.execute(text("""
            UPDATE users 
            SET is_admin = TRUE 
            WHERE id = 1
        """))
        
        conn.commit()
        print("✅ Added is_admin field to users table")


def downgrade():
    """Remove is_admin field from users table"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE users 
            DROP COLUMN is_admin
        """))
        
        conn.commit()
        print("✅ Removed is_admin field from users table")


if __name__ == "__main__":
    upgrade()