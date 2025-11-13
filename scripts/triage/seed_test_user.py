#!/usr/bin/env python3
"""Quick helper to seed a test user via the synchronous DB session.

This avoids passlib/bcrypt issues by writing a user record with an empty
hashed_password. It's intended for local testing only.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import get_db_manager, init_db
from app.models.user import User


def main():
	print("Ensuring sync DB engine and schema...")
	init_db()
	mgr = get_db_manager()
	if mgr.sync_session_factory is None:
		raise RuntimeError("Sync session factory not initialized")

	Session = mgr.sync_session_factory
	session = Session()
	try:
		existing = session.query(User).filter(User.email == "moatasimfarooque@gmail.com").one_or_none()
		if existing:
			print(f"User already exists: {existing.email} (id={existing.id})")
			return

		user = User(
			email="moatasimfarooque@gmail.com",
			username="moatasim",
			hashed_password="",
			skills=[],
			preferred_locations=["Remote", "United States"],
			experience_level="senior",
			is_admin=True,
		)
		session.add(user)
		session.commit()
		print(f"✅ Created user {user.email} (id={user.id})")
	except Exception:
		session.rollback()
		raise
	finally:
		session.close()


if __name__ == "__main__":
	main()
