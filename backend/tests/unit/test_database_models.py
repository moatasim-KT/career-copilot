
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import Base

# Setup a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
    assert user.username == "testuser"


def test_get_user(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    retrieved_user = db.query(User).filter(User.email == "test@example.com").first()
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"


def test_update_user(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    user.email = "new_email@example.com"
    db.add(user)
    db.commit()
    db.refresh(user)

    updated_user = db.query(User).filter(User.id == user.id).first()
    assert updated_user.email == "new_email@example.com"


def test_delete_user(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    db.delete(user)
    db.commit()

    deleted_user = db.query(User).filter(User.id == user.id).first()
    assert deleted_user is None


def test_create_job(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)
    assert job.id is not None
    assert job.company == "TestCo"


def test_get_job(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    retrieved_job = db.query(Job).filter(Job.id == job.id).first()
    assert retrieved_job is not None
    assert retrieved_job.title == "Software Engineer"


def test_update_job(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    job.title = "Senior Software Engineer"
    db.add(job)
    db.commit()
    db.refresh(job)

    updated_job = db.query(Job).filter(Job.id == job.id).first()
    assert updated_job.title == "Senior Software Engineer"


def test_delete_job_cascades_applications(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    application = Application(user_id=user.id, job_id=job.id, status="applied")
    db.add(application)
    db.commit()
    db.refresh(application)

    # Verify application exists
    assert db.query(Application).count() == 1

    db.delete(job)
    db.commit()

    deleted_job = db.query(Job).filter(Job.id == job.id).first()
    assert deleted_job is None

    # Verify application is also deleted due to cascade
    deleted_application = db.query(Application).filter(Application.id == application.id).first()
    assert deleted_application is None


def test_create_application(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    application = Application(user_id=user.id, job_id=job.id, status="interested")
    db.add(application)
    db.commit()
    db.refresh(application)
    assert application.id is not None
    assert application.status == "interested"


def test_get_application(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    application = Application(user_id=user.id, job_id=job.id, status="interested")
    db.add(application)
    db.commit()
    db.refresh(application)

    retrieved_application = db.query(Application).filter(Application.id == application.id).first()
    assert retrieved_application is not None
    assert retrieved_application.status == "interested"


def test_update_application(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    application = Application(user_id=user.id, job_id=job.id, status="interested")
    db.add(application)
    db.commit()
    db.refresh(application)

    application.status = "applied"
    db.add(application)
    db.commit()
    db.refresh(application)

    updated_application = db.query(Application).filter(Application.id == application.id).first()
    assert updated_application.status == "applied"


def test_delete_application(db: SessionLocal):
    user = User(username="testuser", email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()
    db.refresh(user)

    job = Job(user_id=user.id, company="TestCo", title="Software Engineer")
    db.add(job)
    db.commit()
    db.refresh(job)

    application = Application(user_id=user.id, job_id=job.id, status="interested")
    db.add(application)
    db.commit()
    db.refresh(application)

    db.delete(application)
    db.commit()

    deleted_application = db.query(Application).filter(Application.id == application.id).first()
    assert deleted_application is None
