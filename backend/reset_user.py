import asyncio
import os

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.user import User


async def reset_user():
	settings = get_settings()
	db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

	print(f"Connecting to DB: {db_url}")
	engine = create_async_engine(db_url)
	async_session = async_sessionmaker(engine, expire_on_commit=False)

	print(f"Resetting user to: {settings.default_user_email} / {settings.default_user_username}")

	async with async_session() as session:
		# Check for existing users
		result = await session.execute(select(User))
		users = result.scalars().all()
		print(f"Found {len(users)} existing users:")
		for u in users:
			print(f" - {u.username} ({u.email})")

		# Delete all users
		await session.execute(delete(User))
		await session.commit()
		print("Deleted all existing users.")

		# Create fresh default user
		hashed_password = get_password_hash("changeme123")
		new_user = User(
			username="demo",
			email="demo@example.com",
			hashed_password=hashed_password,
			is_admin=True,
			is_active=True,
			skills=["Python", "React"],
			preferred_locations=["Remote"],
			experience_level="senior",
			daily_application_goal=10,
			prefer_remote_jobs=True,
		)
		session.add(new_user)
		await session.commit()
		print(f"Created new user: demo / demo@example.com / changeme123")

	await engine.dispose()


if __name__ == "__main__":
	asyncio.run(reset_user())
