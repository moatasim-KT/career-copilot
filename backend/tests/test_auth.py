import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import create_app
from backend.app.core.database import get_db, Base


def override_get_db(db: Session):
	try:
		yield db
	finally:
		db.close()


@pytest.fixture(scope="module")
def client_fixture(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client


class TestAuth:
	def test_register_and_login(self, client_fixture):
		# Register a new user
		response = client_fixture.post("/api/v1/auth/register", json={"username": "testuser", "email": "test@example.com", "password": "password"})
		assert response.status_code == 200
		data = response.json()
		assert "access_token" in data
		assert data["token_type"] == "bearer"

		# Try to register the same user again
		response = client_fixture.post("/api/v1/auth/register", json={"username": "testuser", "email": "test@example.com", "password": "password"})
		assert response.status_code == 400

		# Log in with the new user
		response = client_fixture.post("/api/v1/auth/login", json={"username": "testuser", "password": "password"})
		assert response.status_code == 200
		data = response.json()
		assert "access_token" in data
		assert data["token_type"] == "bearer"

		# Log in with incorrect password
		response = client_fixture.post("/api/v1/auth/login", json={"username": "testuser", "password": "wrongpassword"})
		assert response.status_code == 401