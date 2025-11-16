import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAuth:
	def test_register_and_login(self, client):
		# Register a new user
		registration_payload = {"username": "testuser", "email": "newuser@example.com", "password": "password"}
		response = client.post("/api/v1/auth/register", json=registration_payload)
		assert response.status_code == 200
		data = response.json()
		assert "access_token" in data
		assert data["token_type"] == "bearer"

		# Try to register the same user again
		response = client.post("/api/v1/auth/register", json=registration_payload)
		assert response.status_code == 400

		# Log in with the new user
		response = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "password"})
		assert response.status_code == 200
		data = response.json()
		assert "access_token" in data
		assert data["token_type"] == "bearer"

		# Log in with incorrect password
		response = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "wrongpassword"})
		assert response.status_code == 401
