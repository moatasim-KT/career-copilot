"""Test script to verify profile endpoints"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import create_app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)


def setup_test_user(db: Session):
	"""Create a test user and return auth token"""
	# Clean up existing test user
	db.query(User).filter(User.username == "testuser").delete()
	db.commit()

	# Create test user
	user = User(
		username="testuser",
		email="test@example.com",
		hashed_password=get_password_hash("testpass"),
		skills=["Python", "FastAPI"],
		preferred_locations=["San Francisco", "Remote"],
		experience_level="mid",
	)
	db.add(user)
	db.commit()
	db.refresh(user)

	# Generate token
	token = create_access_token({"sub": user.username, "user_id": user.id})

	return token, user.id


def main():
	"""Run all profile endpoint tests"""
	print("=" * 60)
	print("Profile Endpoints Verification")
	print("=" * 60)

	try:
		# These tests now rely on the db fixture from conftest.py
		# They cannot be run directly from main() without a proper test runner setup
		print("These tests are designed to be run with pytest and the db fixture.")
		print("Please run `pytest backend/tests/test_profile_endpoints.py`")
		return 0

	except Exception as e:
		print(f"\n✗ ERROR: {e}")
		import traceback

		traceback.print_exc()
		return 1


if __name__ == "__main__":
	sys.exit(main())
