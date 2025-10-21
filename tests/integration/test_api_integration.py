import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import create_app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.security import get_password_hash

# Override settings for testing
from app.core.config import get_settings
settings = get_settings()
settings.database_url = "sqlite:///./test.db"
settings.disable_auth = True # Bypass auth for easier testing

# Create a test client fixture
@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

# Create a test database fixture
@pytest.fixture(scope="function")
def db_session():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Override the get_db dependency to use the test database
@pytest.fixture(scope="function")
def app_with_test_db(client, db_session):
    def override_get_db():
        yield db_session
    client.app.dependency_overrides[get_db] = override_get_db
    yield client
    client.app.dependency_overrides.clear()

# Helper function to create a user
def create_test_user(db: Session, username: str = "testuser", email: str = "test@example.com", password: str = "testpassword") -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
        experience_level="mid",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Helper function to get auth headers
def get_auth_headers(user: User) -> dict:
    # Since disable_auth is True, we don't need a real token
    # But if it were False, we'd generate one here
    return {"Authorization": f"Bearer fake-token-for-{user.username}"}


# --- Test Cases ---

def test_register_and_login_flow(app_with_test_db, db_session):
    # Register
    response = app_with_test_db.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "newpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Login
    response = app_with_test_db.post(
        "/api/v1/auth/login",
        json={"username": "newuser", "password": "newpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_profile_update_and_retrieve_flow(app_with_test_db, db_session):
    user = create_test_user(db_session)
    headers = get_auth_headers(user)

    # Update profile
    update_data = {
        "skills": ["Python", "Django", "AWS"],
        "preferred_locations": ["Remote", "London"],
        "experience_level": "senior",
    }
    response = app_with_test_db.put("/api/v1/profile", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_profile = response.json()
    assert "Django" in updated_profile["skills"]
    assert "London" in updated_profile["preferred_locations"]
    assert updated_profile["experience_level"] == "senior"

    # Retrieve profile
    response = app_with_test_db.get("/api/v1/profile", headers=headers)
    assert response.status_code == 200
    retrieved_profile = response.json()
    assert retrieved_profile["username"] == user.username
    assert "Django" in retrieved_profile["skills"]

def test_job_creation_and_recommendation_flow(app_with_test_db, db_session):
    user = create_test_user(db_session)
    headers = get_auth_headers(user)

    # Create jobs
    job1_data = {
        "company": "TechCo", "title": "Python Dev", "location": "Remote",
        "tech_stack": ["Python", "FastAPI"], "responsibilities": "Build APIs"
    }
    job2_data = {
        "company": "DataCo", "title": "Data Scientist", "location": "New York",
        "tech_stack": ["Python", "Pandas"], "responsibilities": "Analyze data"
    }
    job3_data = {
        "company": "OtherCo", "title": "Java Dev", "location": "London",
        "tech_stack": ["Java", "Spring"], "responsibilities": "Build apps"
    }

    app_with_test_db.post("/api/v1/jobs", json=job1_data, headers=headers)
    app_with_test_db.post("/api/v1/jobs", json=job2_data, headers=headers)
    app_with_test_db.post("/api/v1/jobs", json=job3_data, headers=headers)

    # Get recommendations
    response = app_with_test_db.get("/api/v1/recommendations", headers=headers)
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 2 # Job 3 (Java) should not be recommended
    assert recommendations[0]["title"] == "Python Dev" # Higher match score
    assert recommendations[1]["title"] == "Data Scientist"

def test_skill_gap_analysis_flow(app_with_test_db, db_session):
    user = create_test_user(db_session, skills=["Python", "FastAPI"])
    headers = get_auth_headers(user)

    # Create jobs that introduce skill gaps
    job1_data = {
        "company": "TechCo", "title": "Python Dev", "location": "Remote",
        "tech_stack": ["Python", "FastAPI", "Docker"], "responsibilities": "Build APIs"
    }
    job2_data = {
        "company": "DataCo", "title": "Data Scientist", "location": "New York",
        "tech_stack": ["Python", "Pandas", "SQL"], "responsibilities": "Analyze data"
    }
    app_with_test_db.post("/api/v1/jobs", json=job1_data, headers=headers)
    app_with_test_db.post("/api/v1/jobs", json=job2_data, headers=headers)

    # Get skill gap analysis
    response = app_with_test_db.get("/api/v1/skill-gap", headers=headers)
    assert response.status_code == 200
    analysis = response.json()
    assert "Docker" in analysis["missing_skills"]
    assert "Pandas" in analysis["missing_skills"]
    assert "SQL" in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] < 100
    assert len(analysis["learning_recommendations"]) > 0

def test_application_creation_and_tracking_flow(app_with_test_db, db_session):
    user = create_test_user(db_session)
    headers = get_auth_headers(user)

    # Create a job
    job_data = {
        "company": "AppCo", "title": "App Dev", "location": "Remote",
        "tech_stack": ["React"], "responsibilities": "Build apps"
    }
    response = app_with_test_db.post("/api/v1/jobs", json=job_data, headers=headers)
    job_id = response.json()["id"]

    # Create application
    app_data = {"job_id": job_id, "status": "interested"}
    response = app_with_test_db.post("/api/v1/applications", json=app_data, headers=headers)
    app_id = response.json()["id"]
    assert response.status_code == 200
    assert response.json()["status"] == "interested"

    # Update application status to applied
    update_app_data = {"status": "applied"}
    response = app_with_test_db.put(f"/api/v1/applications/{app_id}", json=update_app_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "applied"

    # Verify job status and date_applied are updated
    updated_job = db_session.query(Job).filter(Job.id == job_id).first()
    assert updated_job.status == "applied"
    assert updated_job.date_applied is not None

    # Get applications list
    response = app_with_test_db.get("/api/v1/applications", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == app_id

def test_full_user_workflow(app_with_test_db, db_session):
    # 1. Register
    response = app_with_test_db.post(
        "/api/v1/auth/register",
        json={"username": "workflowuser", "email": "workflow@example.com", "password": "workflowpassword"}
    )
    assert response.status_code == 200
    login_response = app_with_test_db.post(
        "/api/v1/auth/login",
        json={"username": "workflowuser", "password": "workflowpassword"}
    )
    assert login_response.status_code == 200
    user_id = login_response.json()["user_id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    headers = get_auth_headers(user)

    # 2. Update profile
    profile_update_data = {
        "skills": ["Python", "Django", "AWS"],
        "preferred_locations": ["Remote", "Berlin"],
        "experience_level": "senior",
    }
    response = app_with_test_db.put("/api/v1/profile", json=profile_update_data, headers=headers)
    assert response.status_code == 200

    # 3. Add jobs
    job1_data = {"company": "GlobalTech", "title": "Lead Python Engineer", "location": "Remote", "tech_stack": ["Python", "Django", "AWS"]}
    job2_data = {"company": "LocalDev", "title": "Junior Frontend Dev", "location": "Berlin", "tech_stack": ["JavaScript", "React"]}
    response = app_with_test_db.post("/api/v1/jobs", json=job1_data, headers=headers)
    assert response.status_code == 200
    job1_id = response.json()["id"]
    response = app_with_test_db.post("/api/v1/jobs", json=job2_data, headers=headers)
    assert response.status_code == 200

    # 4. Get recommendations
    response = app_with_test_db.get("/api/v1/recommendations", headers=headers)
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 1 # Only job1 should match well
    assert recommendations[0]["title"] == "Lead Python Engineer"

    # 5. Apply to a job
    app_data = {"job_id": job1_id, "status": "applied"}
    response = app_with_test_db.post("/api/v1/applications", json=app_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "applied"

    # 6. View analytics
    response = app_with_test_db.get("/api/v1/analytics/summary", headers=headers)
    assert response.status_code == 200
    analytics = response.json()
    assert analytics["total_jobs"] == 2
    assert analytics["total_applications"] == 1
    assert analytics["daily_applications_today"] == 1 # Assuming it's run on the same day
