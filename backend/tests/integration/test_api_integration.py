import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import get_db, Base, engine
from app.core.security import create_access_token

# Create a new database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def db_engine():
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="session")
def tables(db_engine):
    Base.metadata.create_all(bind=db_engine)
    yield
    Base.metadata.drop_all(bind=db_engine)

@pytest.fixture
def db_session(db_engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything."""
    connection = db_engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()

@pytest.fixture
def app_with_test_db(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    del app.dependency_overrides[get_db]

@pytest.fixture
def client(app_with_test_db):
    return TestClient(app_with_test_db)

# Helper function to create a user
def create_test_user(db: Session, username: str = "testuser", email: str = "test@example.com", password: str = "pass", skills: list = None) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=password,
        skills=skills or ["Python", "FastAPI"]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_auth_headers(user: User) -> dict:
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}

def test_full_user_workflow(client: TestClient, db_session: Session):
    # 1. Register a new user
    response = client.post("/api/v1/auth/register", json={"username": "workflowuser", "email": "workflow@example.com", "password": "pass"})
    assert response.status_code == 200
    assert "id" in response.json()

    # 2. Login with the new user
    response = client.post("/api/v1/auth/login", json={"username": "workflowuser", "password": "pass"})
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    user_id = response.json()["user_id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    headers = get_auth_headers(user)

    # 3. Update profile
    profile_data = {"skills": ["Python", "FastAPI", "AWS"], "preferred_locations": ["Remote"], "experience_level": "senior"}
    response = client.put("/api/v1/profile", json=profile_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["skills"] == ["Python", "FastAPI", "AWS"]

    # 4. Add jobs
    job1_data = {"company": "GlobalTech", "title": "Lead Python Engineer", "location": "Remote", "tech_stack": ["Python", "Django", "AWS"]}
    job2_data = {"company": "LocalDev", "title": "Junior Frontend Dev", "location": "Berlin", "tech_stack": ["JavaScript", "React"]}
    response = client.post("/api/v1/jobs", json=job1_data, headers=headers)
    assert response.status_code == 200
    job1_id = response.json()["id"]
    response = client.post("/api/v1/jobs", json=job2_data, headers=headers)
    assert response.status_code == 200

    # 5. Get recommendations
    response = client.get("/api/v1/recommendations", headers=headers)
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) > 0 # At least one job should match

    # 6. Apply to a job
    app_data = {"job_id": job1_id, "status": "applied"}
    response = client.post("/api/v1/applications", json=app_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "applied"

    # 7. Get analytics
    response = client.get("/api/v1/analytics/summary", headers=headers)
    assert response.status_code == 200
    analytics = response.json()
    assert analytics["total_jobs"] == 2
    assert analytics["total_applications"] == 1

    # 8. Get skill gap analysis
    response = client.get("/api/v1/skill-gap", headers=headers)
    assert response.status_code == 200
    skill_gap_analysis = response.json()
    assert "user_skills" in skill_gap_analysis
    assert "missing_skills" in skill_gap_analysis
    assert "skill_coverage_percentage" in skill_gap_analysis
    assert "learning_recommendations" in skill_gap_analysis
