import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import create_app
from backend.app.core.database import get_db
from backend.app.models.user import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


class TestAuth(unittest.TestCase):
	def test_register_and_login(self):
		# Register a new user
		response = client.post("/api/v1/auth/register", json={"username": "testuser", "email": "test@example.com", "password": "password"})
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertIn("access_token", data)
		self.assertEqual(data["token_type"], "bearer")

		# Try to register the same user again
		response = client.post("/api/v1/auth/register", json={"username": "testuser", "email": "test@example.com", "password": "password"})
		self.assertEqual(response.status_code, 400)

		# Log in with the new user
		response = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "password"})
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertIn("access_token", data)
		self.assertEqual(data["token_type"], "bearer")

		# Log in with incorrect password
		response = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "wrongpassword"})
		self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
	unittest.main()
