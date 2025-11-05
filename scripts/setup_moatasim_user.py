"""
Setup Moatasim as the single user and delete all others
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def setup_moatasim_user():
	"""Delete all users except Moatasim and set up his profile"""

	# Create async engine
	engine = create_async_engine(str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://"), echo=False)

	async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

	async with async_session() as db:
		try:
			print("🔧 Setting up Moatasim's user account...")

			# First, check if Moatasim's user exists
			result = await db.execute(select(User).where(User.email == "moatasimfarooque@gmail.com"))
			moatasim_user = result.scalar_one_or_none()

			if moatasim_user:
				print(f"✅ Found existing user: {moatasim_user.email} (ID: {moatasim_user.id})")
				moatasim_id = moatasim_user.id
			else:
				# Create Moatasim's user account
				print("Creating new user account for moatasimfarooque@gmail.com...")
				moatasim_user = User(
					email="moatasimfarooque@gmail.com",
					username="moatasim",
					hashed_password=get_password_hash("not_needed_single_user_mode"),
					skills=[],  # Will be populated from resume
					preferred_locations=["Remote", "United States"],
					experience_level="senior",
					is_admin=True,
				)
				db.add(moatasim_user)
				await db.flush()
				moatasim_id = moatasim_user.id
				print(f"✅ Created user: {moatasim_user.email} (ID: {moatasim_id})")

			# Get all other users
			result = await db.execute(select(User).where(User.id != moatasim_id))
			other_users = result.scalars().all()

			if other_users:
				print(f"\n🗑️  Deleting {len(other_users)} other users and ALL their data...")
				other_user_ids = [user.id for user in other_users]

				# Delete all related data in correct order (respecting foreign keys)
				from app.models.resume_upload import ResumeUpload

				print("   - Deleting resume uploads...")
				for user_id in other_user_ids:
					await db.execute(delete(ResumeUpload).where(ResumeUpload.user_id == user_id))

				print("   - Deleting applications...")
				for user_id in other_user_ids:
					await db.execute(delete(Application).where(Application.user_id == user_id))

				print("   - Deleting jobs...")
				for user_id in other_user_ids:
					await db.execute(delete(Job).where(Job.user_id == user_id))

				print("   - Deleting users...")
				for user in other_users:
					await db.execute(delete(User).where(User.id == user.id))

				await db.commit()
				print(f"✅ Deleted {len(other_users)} users and all their data")
			else:
				print("✅ No other users to delete")

			# Transfer any orphaned jobs/applications to Moatasim
			result = await db.execute(select(Job).where(Job.user_id != moatasim_id))
			orphaned_jobs = result.scalars().all()

			if orphaned_jobs:
				print(f"\n📦 Transferring {len(orphaned_jobs)} orphaned jobs to Moatasim...")
				for job in orphaned_jobs:
					job.user_id = moatasim_id
				await db.commit()
				print(f"✅ Transferred {len(orphaned_jobs)} jobs")

			# Count final data
			result = await db.execute(select(User))
			total_users = len(result.scalars().all())

			result = await db.execute(select(Job).where(Job.user_id == moatasim_id))
			total_jobs = len(result.scalars().all())

			result = await db.execute(select(Application).where(Application.user_id == moatasim_id))
			total_applications = len(result.scalars().all())

			print("\n" + "=" * 60)
			print("🎉 Setup Complete!")
			print("=" * 60)
			print(f"Total users in database: {total_users}")
			print(f"Jobs for Moatasim: {total_jobs}")
			print(f"Applications for Moatasim: {total_applications}")
			print("\nUser Account:")
			print(f"  Email: moatasimfarooque@gmail.com")
			print(f"  Username: moatasim")
			print(f"  User ID: {moatasim_id}")
			print(f"  Skills: {moatasim_user.skills or 'To be populated from resume'}")
			print("\n💡 Next step: Upload your resume to populate skills and experience")
			print("=" * 60)

		except Exception as e:
			print(f"\n❌ Error: {e}")
			await db.rollback()
			raise


if __name__ == "__main__":
	asyncio.run(setup_moatasim_user())
