#!/usr/bin/env python3
"""
Debug authentication issues
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.user import User
from app.core.security import get_password_hash, verify_password

def main():
    """Debug authentication"""
    print("🔍 Debugging Authentication Issues")
    print("=" * 50)
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"✅ Database connection OK - {user_count} users found")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Check if testuser exists
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        if user:
            print(f"✅ User 'testuser' exists with ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Created: {user.created_at}")
            
            # Test password verification
            test_password = "testpassword123"
            if verify_password(test_password, user.hashed_password):
                print("✅ Password verification works")
            else:
                print("❌ Password verification failed")
                print(f"   Stored hash: {user.hashed_password[:50]}...")
                
                # Try to update password
                new_hash = get_password_hash(test_password)
                user.hashed_password = new_hash
                db.commit()
                print("✅ Password hash updated")
        else:
            print("❌ User 'testuser' not found")
            
            # Create the user
            new_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword123")
            )
            db.add(new_user)
            db.commit()
            print("✅ User 'testuser' created")
            
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()