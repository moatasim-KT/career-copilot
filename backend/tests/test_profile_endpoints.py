"""Test script to verify profile endpoints"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import create_app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_profile.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
	try:
		db = TestingSessionLocal()
		yield db
	finally:
		db.close()


app = create_app()
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_test_user():
	"""Create a test user and return auth token"""
	db = TestingSessionLocal()

	# Clean up existing test user
	db.query(User).filter(User.username == "testuser").delete()
	db.commit()

	# Create test user
	user = User(
		username="testuser",
		email="test@example.com",
		hashed_password=get_password_hash("testpass123"),
		skills=["Python", "FastAPI"],
		preferred_locations=["San Francisco", "Remote"],
		experience_level="mid",
	)
	db.add(user)
	db.commit()
	db.refresh(user)

	# Generate token
	token = create_access_token({"sub": user.username, "user_id": user.id})

	db.close()
	return token, user.id


def test_get_profile():
	"""Test GET /api/v1/profile endpoint"""
	print("\n=== Testing GET /api/v1/profile ===")

	token, _user_id = setup_test_user()
	headers = {"Authorization": f"Bearer {token}"}

	response = client.get("/api/v1/profile", headers=headers)

	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	print(f"✓ Status code: {response.status_code}")

	data = response.json()

	# Verify response structure
	assert "id" in data, "Response should contain id"
	assert "username" in data, "Response should contain username"
	assert "email" in data, "Response should contain email"
	assert "skills" in data, "Response should contain skills"
	assert "preferred_locations" in data, "Response should contain preferred_locations"
	assert "experience_level" in data, "Response should contain experience_level"
	print(f"✓ Response contains all required fields")

	# Verify data
	assert data["username"] == "testuser", "Username should match"
	assert data["email"] == "test@example.com", "Email should match"
	assert data["skills"] == ["Python", "FastAPI"], "Skills should match"
	assert data["preferred_locations"] == ["San Francisco", "Remote"], "Locations should match"
	assert data["experience_level"] == "mid", "Experience level should match"
	print(f"✓ Profile data is correct")
	print(f"  Username: {data['username']}")
	print(f"  Email: {data['email']}")
	print(f"  Skills: {data['skills']}")
	print(f"  Locations: {data['preferred_locations']}")
	print(f"  Experience: {data['experience_level']}")

	return True


def test_get_profile_unauthorized():
	"""Test GET /api/v1/profile without authentication"""
	print("\n=== Testing GET /api/v1/profile (Unauthorized) ===")

	response = client.get("/api/v1/profile")

	assert response.status_code == 401, f"Expected 401, got {response.status_code}"
	print(f"✓ Unauthorized request correctly rejected with status {response.status_code}")

	return True


def test_update_profile():
	"""Test PUT /api/v1/profile endpoint"""
	print("\n=== Testing PUT /api/v1/profile ===")

	token, _user_id = setup_test_user()
	headers = {"Authorization": f"Bearer {token}"}

	# Update profile
	update_data = {
		"skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
		"preferred_locations": ["New York", "Boston", "Remote"],
		"experience_level": "senior",
	}

	response = client.put("/api/v1/profile", json=update_data, headers=headers)

	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	print(f"✓ Status code: {response.status_code}")

	data = response.json()

	# Verify updated data
	assert data["skills"] == update_data["skills"], "Skills should be updated"
	assert data["preferred_locations"] == update_data["preferred_locations"], "Locations should be updated"
	assert data["experience_level"] == update_data["experience_level"], "Experience level should be updated"
	print(f"✓ Profile updated successfully")
	print(f"  New skills: {data['skills']}")
	print(f"  New locations: {data['preferred_locations']}")
	print(f"  New experience: {data['experience_level']}")

	# Verify persistence by fetching again
	response = client.get("/api/v1/profile", headers=headers)
	data = response.json()

	assert data["skills"] == update_data["skills"], "Updated skills should persist"
	assert data["preferred_locations"] == update_data["preferred_locations"], "Updated locations should persist"
	assert data["experience_level"] == update_data["experience_level"], "Updated experience should persist"
	print(f"✓ Updated profile persisted correctly")

	return True


def test_update_profile_partial():
	"""Test PUT /api/v1/profile with partial update"""
	print("\n=== Testing PUT /api/v1/profile (Partial Update) ===")

	token, _user_id = setup_test_user()
	headers = {"Authorization": f"Bearer {token}"}

	# Get current profile
	response = client.get("/api/v1/profile", headers=headers)
	original_data = response.json()

	# Update only skills
	update_data = {"skills": ["JavaScript", "React", "Node.js"]}

	response = client.put("/api/v1/profile", json=update_data, headers=headers)

	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	print(f"✓ Status code: {response.status_code}")

	data = response.json()

	# Verify only skills changed
	assert data["skills"] == update_data["skills"], "Skills should be updated"
	assert data["preferred_locations"] == original_data["preferred_locations"], "Locations should remain unchanged"
	assert data["experience_level"] == original_data["experience_level"], "Experience should remain unchanged"
	print(f"✓ Partial update successful")
	print(f"  Updated skills: {data['skills']}")
	print(f"  Unchanged locations: {data['preferred_locations']}")
	print(f"  Unchanged experience: {data['experience_level']}")

	return True


def test_update_profile_invalid_experience():
	"""Test PUT /api/v1/profile with invalid experience level"""
	print("\n=== Testing PUT /api/v1/profile (Invalid Experience Level) ===")

	token, _user_id = setup_test_user()
	headers = {"Authorization": f"Bearer {token}"}

	# Try to update with invalid experience level
	update_data = {
		"experience_level": "expert"  # Invalid - should be junior, mid, or senior
	}

	response = client.put("/api/v1/profile", json=update_data, headers=headers)

	assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
	print(f"✓ Invalid experience level correctly rejected with status {response.status_code}")

	return True


def test_update_profile_unauthorized():
	"""Test PUT /api/v1/profile without authentication"""
	print("\n=== Testing PUT /api/v1/profile (Unauthorized) ===")

	update_data = {"skills": ["Hacking"]}

	response = client.put("/api/v1/profile", json=update_data)

	assert response.status_code == 401, f"Expected 401, got {response.status_code}"
	print(f"✓ Unauthorized request correctly rejected with status {response.status_code}")

	return True


def cleanup():
	"""Clean up test database"""
	try:
		os.remove("./test_profile.db")
		print("\n✓ Test database cleaned up")
	except:
		pass


def main():
	"""Run all profile endpoint tests"""
	print("=" * 60)
	print("Profile Endpoints Verification")
	print("=" * 60)

	try:
		test_get_profile()
		test_get_profile_unauthorized()
		test_update_profile()
		test_update_profile_partial()
		test_update_profile_invalid_experience()
		test_update_profile_unauthorized()

		print("\n" + "=" * 60)
		print("✓ ALL TESTS PASSED")
		print("=" * 60)
		print("\nVerification Summary:")
		print("  ✓ GET /api/v1/profile returns user profile")
		print("  ✓ PUT /api/v1/profile updates user profile")
		print("  ✓ Partial updates work correctly")
		print("  ✓ Experience level validation works")
		print("  ✓ Authorization is enforced")
		print("=" * 60)

		cleanup()
		return 0

	except AssertionError as e:
		print(f"\n✗ TEST FAILED: {e}")
		cleanup()
		return 1
	except Exception as e:
		print(f"\n✗ ERROR: {e}")
		import traceback

		traceback.print_exc()
		cleanup()
		return 1


if __name__ == "__main__":
	sys.exit(main())
	sys.exit(main())
