#!/usr/bin/env python3
"""Create a test user for authentication testing"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("✓ Test user already exists")
            print("  Username: testuser")
            print(f"  Email: {existing_user.email}")
            return

        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User",
            experience_level="Mid",
            current_role="Software Engineer",
            skills=["Python", "JavaScript", "React", "FastAPI"],
            location="Remote",
            remote_preference=True,
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print("✅ Test user created successfully!")
        print("  Username: testuser")
        print("  Password: testpass")
        print(f"  Email: {test_user.email}")
        print(f"  ID: {test_user.id}")

    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
