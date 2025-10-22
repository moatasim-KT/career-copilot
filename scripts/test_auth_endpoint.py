#!/usr/bin/env python3
"""
Test authentication endpoint directly
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

def main():
    """Test authentication endpoint"""
    print("🔍 Testing Authentication Endpoint")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Test health endpoint first
    try:
        response = client.get("/api/v1/health")
        print(f"Health endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test registration
    try:
        register_data = {
            "username": "testuser2",
            "email": "test2@example.com", 
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/register", json=register_data)
        print(f"Register endpoint: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            print("✅ Registration successful")
    except Exception as e:
        print(f"❌ Registration failed: {e}")
    
    # Test login
    try:
        login_data = {
            "username": "testuser2",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"Login endpoint: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            result = response.json()
            print("✅ Login successful")
            print(f"Token: {result.get('access_token', 'No token')[:50]}...")
    except Exception as e:
        print(f"❌ Login failed: {e}")

if __name__ == "__main__":
    main()