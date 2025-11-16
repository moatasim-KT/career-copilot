#!/usr/bin/env python
"""Setup test database schema."""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base


async def setup():
	engine = create_async_engine("postgresql+asyncpg://moatasimfarooque@localhost:5432/career_copilot_test")
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	await engine.dispose()
	print("Schema created successfully")


if __name__ == "__main__":
	asyncio.run(setup())
