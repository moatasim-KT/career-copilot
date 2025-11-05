#!/usr/bin/env python3
"""Update first user to 'Moatasim' with full admin permissions"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import after adding backend to path
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def update_user_to_moatasim():
	"""Update first user to Moatasim with admin permissions"""
	# Use PostgreSQL database
	DATABASE_URL = "postgresql+asyncpg://moatasimfarooque@localhost:5432/career_copilot"

	engine = create_async_engine(DATABASE_URL, echo=False)
	async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

	async with async_session() as db:
		try:
			# Get the first user
			result = await db.execute(select(User).where(User.id == 338))
			user = result.scalar_one_or_none()

			if not user:
				print("❌ User with ID 338 not found!")
				print("   Trying to get the first user...")
				result = await db.execute(select(User).limit(1))
				user = result.scalar_one_or_none()

				if not user:
					print("❌ No users found in database!")
					print("   Please create a user first.")
					return

			print("=" * 60)
			print("📝 Current User Details:")
			print("=" * 60)
			print(f"   ID: {user.id}")
			print(f"   Username: {user.username}")
			print(f"   Email: {user.email}")
			print(f"   Admin: {user.is_admin}")
			print("=" * 60)

			# Update user details
			user.username = "Moatasim"
			user.email = "moatasimfarooque@gmail.com"
			user.hashed_password = get_password_hash("moatasim123")
			user.is_admin = True
			user.experience_level = "mid"  # Must be 'junior', 'mid', or 'senior'
			user.skills = [
				"Python",
				"Machine Learning",
				"Data Science",
				"FastAPI",
				"React",
				"TypeScript",
				"PostgreSQL",
				"Docker",
				"Kubernetes",
				"AWS",
			]
			# EU locations based on configured scrapers
			user.preferred_locations = [
				"Berlin",
				"Munich",
				"Amsterdam",
				"London",
				"Paris",
				"Dublin",
				"Barcelona",
				"Stockholm",
				"Copenhagen",
				"Remote",
			]
			user.daily_application_goal = 15

			await db.commit()
			await db.refresh(user)
			await db.refresh(user)

			print("\n✅ User Updated Successfully!")
			print("=" * 60)
			print("📋 New User Details:")
			print("=" * 60)
			print(f"   ID: {user.id}")
			print(f"   Username: {user.username}")
			print(f"   Email: {user.email}")
			print(f"   Password: moatasim123")
			print(f"   Admin: {user.is_admin} ✅")
			print(f"   Experience Level: {user.experience_level}")
			print(f"   Skills: {', '.join(user.skills[:5])}... ({len(user.skills)} total)")
			print(f"   Preferred Locations: {', '.join(user.preferred_locations[:5])}... ({len(user.preferred_locations)} total)")
			print(f"   Daily Goal: {user.daily_application_goal} applications")
			print("=" * 60)
			print("\n🎉 All Permissions Granted!")
			print("=" * 60)
			print("   ✅ Admin Access: Full system control")
			print("   ✅ User Management: Create/edit/delete users")
			print("   ✅ Job Management: Full CRUD operations")
			print("   ✅ Application Tracking: Complete access")
			print("   ✅ Analytics: All reports and insights")
			print("   ✅ Settings: System configuration")
			print("=" * 60)
			print("\n🌍 EU Locations Configured:")
			print("=" * 60)
			for loc in user.preferred_locations:
				print(f"   • {loc}")
			print("=" * 60)
			print(f"\n🌐 Login at: http://localhost:3000")
			print("   Username: Moatasim")
			print("   Password: moatasim123")
			print("=" * 60)

		except Exception as e:
			print(f"❌ Error: {e}")
			import traceback

			traceback.print_exc()
			await db.rollback()
		finally:
			await engine.dispose()


if __name__ == "__main__":
	asyncio.run(update_user_to_moatasim())
