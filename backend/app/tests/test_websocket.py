
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User

client = TestClient(app)

def test_websocket_connection():
    with client.websocket_connect("/ws") as websocket:
        assert websocket.scope['type'] == 'websocket'

def test_websocket_authentication():
    # Create a dummy user and token for testing
    user = User(id=1, username="testuser", email="test@example.com", hashed_password="test")
    token = create_access_token(data={"sub": user.username})

    with client.websocket_connect("/ws", headers={'Authorization': f'Bearer {token}'}) as websocket:
        # For TestClient, the authentication is handled at connection time via headers
        # We can send a dummy message to ensure the connection is active
        websocket.send_text("Hello")
        response = websocket.receive_text()
        assert response == "Hello"
