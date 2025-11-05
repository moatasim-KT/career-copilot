#!/usr/bin/env python3
"""Create user 'moatasim' for easy login"""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import after adding backend to path
from app.core.security import get_password_hash
from app.models.user import User

# Use SQLite database
DATABASE_URL = "sqlite:///./backend/data/career_copilot.db"


def create_moatasim_user():
    """Create moatasim user"""
    engine = create_engine(DATABASE_URL.replace("sqlite:///./backend/", "sqlite:///./"))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.username == "moatasim").first()
        if existing:
            print("✅ User 'moatasim' already exists!")
            print("   Username: moatasim")
            print(f"   Email: {existing.email}")
            print("   Password: moatasim123")
            return

        # Create new user
        new_user = User(
            username="moatasim",
            email="moatasim@example.com",
            hashed_password=get_password_hash("moatasim123"),
            experience_level="Senior",
            skills=["Python", "Machine Learning", "FastAPI", "React"],
            preferred_locations=["Remote", "San Francisco", "New York"],
            daily_application_goal=10,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("=" * 50)
        print("✅ User Created Successfully!")
        print("=" * 50)
        print("Username: moatasim")
        print("Password: moatasim123")
        print(f"Email: {new_user.email}")
        print(f"User ID: {new_user.id}")
        print("=" * 50)
        print("\nYou can now login at: http://localhost:3000")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_moatasim_user()
