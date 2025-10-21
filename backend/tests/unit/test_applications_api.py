"""Tests for application API endpoints"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.security import create_access_token


def create_user(db: Session, username: str = "testuser", email: str = "test@example.com") -> User:
    """Create a test user"""
    user = User(username=username, email=email, hashed_password="fake_password")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_job(db: Session, user_id: int, company: str = "Test Inc", title: str = "Software Engineer") -> Job:
    """Create a test job"""
    job = Job(user_id=user_id, company=company, title=title, status="active")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_auth_headers(user_id: int, username: str) -> dict:
    """Get authentication headers for testing"""
    token = create_access_token({"sub": username, "user_id": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_create_application(client: TestClient, db: Session):
    """Test creating a new application"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Test data
    application_data = {
        "job_id": job.id,
        "status": "interested",
        "notes": "Test application"
    }
    
    response = client.post("/api/v1/applications/", json=application_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job.id
    assert data["status"] == "interested"
    assert data["notes"] == "Test application"
    assert data["user_id"] == user.id


def test_list_applications(client: TestClient, db: Session):
    """Test listing applications"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Create test application
    application = Application(
        user_id=user.id,
        job_id=job.id,
        status="applied",
        notes="Test application"
    )
    db.add(application)
    db.commit()
    
    response = client.get("/api/v1/applications/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "applied"
    assert data[0]["notes"] == "Test application"


def test_update_application_status_to_applied(client: TestClient, db: Session):
    """Test updating application status to 'applied' updates job status and date"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Create test application with initial status
    application = Application(
        user_id=user.id,
        job_id=job.id,
        status="interested",
        notes="Test application"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Update application status to 'applied'
    update_data = {"status": "applied"}
    response = client.put(f"/api/v1/applications/{application.id}", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "applied"
    
    # Verify job was updated
    db.refresh(job)
    assert job.status == "applied"
    assert job.date_applied is not None


def test_status_validation(client: TestClient, db: Session):
    """Test that invalid status values are rejected"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Test invalid status in create
    invalid_data = {
        "job_id": job.id,
        "status": "invalid_status",
        "notes": "Test application"
    }
    
    response = client.post("/api/v1/applications/", json=invalid_data, headers=headers)
    assert response.status_code == 422  # Validation error


def test_status_transitions(client: TestClient, db: Session):
    """Test various status transitions"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Create test application
    application = Application(
        user_id=user.id,
        job_id=job.id,
        status="interested",
        notes="Test application"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Test valid status transitions
    valid_statuses = ["applied", "interview", "offer", "accepted", "rejected", "declined"]
    
    for status in valid_statuses:
        update_data = {"status": status}
        response = client.put(f"/api/v1/applications/{application.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == status


def test_application_not_found(client: TestClient, db: Session):
    """Test handling of non-existent application"""
    user = create_user(db)
    headers = get_auth_headers(user.id, user.username)
    
    # Try to update non-existent application
    response = client.put("/api/v1/applications/999", json={"status": "applied"}, headers=headers)
    assert response.status_code == 404
    assert "Application not found" in response.json()["detail"]


def test_duplicate_application_prevention(client: TestClient, db: Session):
    """Test that duplicate applications for the same job are prevented"""
    user = create_user(db)
    job = create_job(db, user.id)
    headers = get_auth_headers(user.id, user.username)
    
    # Create first application
    application = Application(
        user_id=user.id,
        job_id=job.id,
        status="applied"
    )
    db.add(application)
    db.commit()
    
    # Try to create duplicate application
    duplicate_data = {
        "job_id": job.id,
        "status": "interested"
    }
    
    response = client.post("/api/v1/applications/", json=duplicate_data, headers=headers)
    assert response.status_code == 400
    assert "Application already exists" in response.json()["detail"]