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
    
    print("Testing /api/v1/health endpoint...")
    response = client.get("/api/v1/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert "timestamp" in data, "Response missing 'timestamp' field"
    assert "components" in data, "Response missing 'components' field"
    assert "database" in data["components"], "Response missing 'database' component"
    assert "scheduler" in data["components"], "Response missing 'scheduler' component"
    
    print("✅ Health check endpoint test passed!")
    print(f"Overall Status: {data['status']}")
    print(f"Database: {data['components']['database']}")
    print(f"Scheduler: {data['components']['scheduler']}")
    
    return data

def test_health_db_endpoint():
    """Test the database-specific health check endpoint"""
    client = TestClient(app)
    
    print("\nTesting /api/v1/health/db endpoint...")
    response = client.get("/api/v1/health/db")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert "database" in data, "Response missing 'database' field"
    assert "timestamp" in data, "Response missing 'timestamp' field"
    
    print("✅ Database health check endpoint test passed!")
    print(f"Database Status: {data['database']}")
    
    return data

if __name__ == "__main__":
    try:
        test_health_endpoint()
        test_health_db_endpoint()
        print("\n✅ All health check tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
