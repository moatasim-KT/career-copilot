"""
Test script for health check endpoint
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    """Test the health check endpoint"""
    client = TestClient(app)
    
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert "timestamp" in data, "Response missing 'timestamp' field"
    assert "components" in data, "Response missing 'components' field"
    assert "database" in data["components"], "Response missing 'database' component"
    assert "scheduler" in data["components"], "Response missing 'scheduler' component"
    

def test_health_db_endpoint():
    """Test the database-specific health check endpoint"""
    client = TestClient(app)
    
    response = client.get("/api/v1/health/db")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert "database" in data, "Response missing 'database' field"
    assert "timestamp" in data, "Response missing 'timestamp' field"
