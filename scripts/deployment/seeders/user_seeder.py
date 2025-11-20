"""
User seeder
"""
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

def seed_users(db: Session) -> User:
    """Create a test user with sample profile"""
    logger.info("Creating test user...")

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        skills=["Python", "JavaScript", "React", "FastAPI", "PostgreSQL", "Docker"],
        preferred_locations=["San Francisco, CA", "New York, NY", "Remote"],
        experience_level="mid",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"✅ Created user: {user.username} (ID: {user.id})")
    return user
