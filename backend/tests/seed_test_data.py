"""
Database seeding script for tests.
Creates essential test data including test user with id=1.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, engine, init_db
from app.core.security import get_password_hash
from app.models.user import User


async def seed_test_user(session: AsyncSession) -> User:
	"""
	Create or update the test user with id=1.
	This user is referenced by many tests.
	"""
	# Check if user with id=1 exists
	result = await session.execute(select(User).where(User.id == 1))
	user = result.scalars().first()

	if user:
		print("✓ Test user (id=1) already exists")
		print(f"  Username: {user.username}")
		print(f"  Email: {user.email}")
		return user

	# Create test user
	user = User(
		id=1,
		username="test_user",
		        email="test@example.com",
		        hashed_password=get_password_hash("testpass"),		skills=["Python", "FastAPI", "JavaScript", "React", "TypeScript", "Docker"],
		preferred_locations=["Remote", "San Francisco", "New York", "Austin"],
		experience_level="senior",
		daily_application_goal=10,
		is_admin=False,
		prefer_remote_jobs=True,
	)

	session.add(user)
	await session.commit()
	await session.refresh(user)

	print("✓ Created test user (id=1)")
	print(f"  Username: {user.username}")
	print(f"  Email: {user.email}")
	print(f"  Skills: {', '.join(user.skills)}")

	return user


async def seed_additional_test_users(session: AsyncSession):
	"""
	Create additional test users for testing various scenarios.
	"""
	test_users = [
		{
			"username": "junior_dev",
			"email": "junior@example.com",
			"skills": ["Python", "JavaScript"],
			"experience_level": "junior",
			"preferred_locations": ["Remote"],
		},
		{
			"username": "senior_engineer",
			"email": "senior@example.com",
			"skills": ["Python", "Go", "Kubernetes", "AWS"],
			"experience_level": "senior",
			"preferred_locations": ["San Francisco", "Seattle"],
		},
		{
			"username": "mid_level",
			"email": "mid@example.com",
			"skills": ["JavaScript", "React", "Node.js"],
			"experience_level": "mid",
			"preferred_locations": ["New York", "Boston"],
		},
	]

	created_count = 0
	for user_data in test_users:
		# Check if user already exists
		result = await session.execute(select(User).where(User.email == user_data["email"]))
		existing_user = result.scalars().first()

		if existing_user:
			continue

		user = User(
			username=user_data["username"],
			email=user_data["email"],
			hashed_password=get_password_hash("testpass"),
			skills=user_data["skills"],
			preferred_locations=user_data["preferred_locations"],
			experience_level=user_data["experience_level"],
			daily_application_goal=5,
			is_admin=False,
			prefer_remote_jobs=True,
		)

		session.add(user)
		created_count += 1

	if created_count > 0:
		await session.commit()
		print(f"✓ Created {created_count} additional test users")
	else:
		print("✓ Additional test users already exist")


async def main():
	"""Run database seeding."""
	print("🌱 Seeding test database...")
	print("-" * 50)

	# Initialize database (create tables if needed)
	await init_db()

	# Create session and seed data
	async with async_session_maker() as session:
		try:
			# Seed primary test user (id=1)
			await seed_test_user(session)

			# Seed additional test users
			await seed_additional_test_users(session)

			print("-" * 50)
			print("✅ Database seeding completed successfully!")

		except Exception as e:
			print(f"❌ Error seeding database: {e}")
			await session.rollback()
			raise


if __name__ == "__main__":
	asyncio.run(main())
