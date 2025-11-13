# Testing Knowledge Base

This knowledge base documents testing strategies, patterns, and best practices for the Career Copilot project. It covers unit testing, integration testing, end-to-end testing, and testing infrastructure.

## Testing Overview

### Testing Pyramid
Career Copilot follows a testing pyramid approach:

```
End-to-End Tests (E2E)     ████░░  (20-30 tests)
Integration Tests         ████████ (60-80 tests)
Unit Tests               ██████████ (200+ tests)
```

### Test Categories

#### 1. Unit Tests
- **Purpose**: Test individual functions, methods, and classes in isolation
- **Scope**: Single function/method/class
- **Dependencies**: Mocked/stubbed
- **Speed**: Fast (< 100ms per test)
- **Coverage**: 80%+ line coverage target

#### 2. Integration Tests
- **Purpose**: Test interaction between components
- **Scope**: Multiple classes/functions working together
- **Dependencies**: Real database, external services (may be mocked)
- **Speed**: Medium (100ms - 1s per test)
- **Coverage**: Key integration points

#### 3. End-to-End Tests
- **Purpose**: Test complete user workflows
- **Scope**: Full application stack
- **Dependencies**: Real services, database
- **Speed**: Slow (1-10s per test)
- **Coverage**: Critical user journeys

## Backend Testing

### Unit Testing Patterns

#### Service Layer Testing
```python
# backend/tests/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def user_service(self, mock_db):
        """User service instance with mocked database"""
        return UserService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing"""
        return User(
            id=1,
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )

    def test_get_user_by_email_success(self, user_service, mock_db, sample_user):
        """Test successful user retrieval by email"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        # Act
        result = user_service.get_user_by_email("test@example.com")

        # Assert
        assert result == sample_user
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()

    def test_get_user_by_email_not_found(self, user_service, mock_db):
        """Test user retrieval when user doesn't exist"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = user_service.get_user_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    def test_create_user_success(self, user_service, mock_db):
        """Test successful user creation"""
        # Arrange
        user_data = UserCreate(
            email="new@example.com",
            password="password123"
        )

        created_user = User(
            id=2,
            email="new@example.com",
            hashed_password="hashed_password",
            is_active=True
        )

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch('app.services.user_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"

            # Act
            result = user_service.create_user(user_data)

            # Assert
            assert result.email == "new@example.com"
            assert result.hashed_password == "hashed_password"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_user_duplicate_email(self, user_service, mock_db, sample_user):
        """Test user creation with duplicate email"""
        # Arrange
        user_data = UserCreate(
            email="test@example.com",  # Existing email
            password="password123"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(user_data)

    def test_authenticate_user_success(self, user_service, mock_db, sample_user):
        """Test successful user authentication"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        with patch('app.services.user_service.verify_password') as mock_verify:
            mock_verify.return_value = True

            # Act
            result = user_service.authenticate_user("test@example.com", "password123")

            # Assert
            assert result == sample_user

    def test_authenticate_user_wrong_password(self, user_service, mock_db, sample_user):
        """Test authentication with wrong password"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user

        with patch('app.services.user_service.verify_password') as mock_verify:
            mock_verify.return_value = False

            # Act
            result = user_service.authenticate_user("test@example.com", "wrongpassword")

            # Assert
            assert result is None

    def test_authenticate_user_not_found(self, user_service, mock_db):
        """Test authentication when user doesn't exist"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = user_service.authenticate_user("nonexistent@example.com", "password123")

        # Assert
        assert result is None
```

#### Repository Testing
```python
# backend/tests/test_application_repository.py
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.repositories.application_repository import ApplicationRepository
from app.models.application import Application
from app.models.user import User
from app.models.job import Job

class TestApplicationRepository:
    @pytest.fixture
    def db_session(self):
        """Database session fixture"""
        # Setup test database session
        pass

    @pytest.fixture
    def repo(self, db_session):
        """Repository instance"""
        return ApplicationRepository(db_session)

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(email="test@example.com", hashed_password="hash")
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_job(self, db_session):
        """Create test job"""
        job = Job(title="Software Engineer", company="Test Corp")
        db_session.add(job)
        db_session.commit()
        return job

    def test_get_user_applications(self, repo, db_session, test_user, test_job):
        """Test getting user applications"""
        # Create test applications
        app1 = Application(user_id=test_user.id, job_id=test_job.id, status="applied")
        app2 = Application(user_id=test_user.id, job_id=test_job.id, status="interviewing")
        db_session.add_all([app1, app2])
        db_session.commit()

        # Act
        applications = repo.get_user_applications(test_user.id)

        # Assert
        assert len(applications) == 2
        assert all(app.user_id == test_user.id for app in applications)
        # Should be ordered by created_at desc
        assert applications[0].created_at >= applications[1].created_at

    def test_get_applications_by_status(self, repo, db_session, test_user, test_job):
        """Test filtering applications by status"""
        # Create applications with different statuses
        app1 = Application(user_id=test_user.id, job_id=test_job.id, status="applied")
        app2 = Application(user_id=test_user.id, job_id=test_job.id, status="rejected")
        app3 = Application(user_id=test_user.id, job_id=test_job.id, status="applied")
        db_session.add_all([app1, app2, app3])
        db_session.commit()

        # Act
        applied_apps = repo.get_applications_by_status("applied")

        # Assert
        assert len(applied_apps) == 2
        assert all(app.status == "applied" for app in applied_apps)

    def test_get_application_stats(self, repo, db_session, test_user, test_job):
        """Test application statistics calculation"""
        # Create applications with different statuses
        statuses = ["applied", "interviewing", "rejected", "applied", "offered"]
        for status in statuses:
            app = Application(user_id=test_user.id, job_id=test_job.id, status=status)
            db_session.add(app)
        db_session.commit()

        # Act
        stats = repo.get_application_stats(test_user.id)

        # Assert
        assert stats["total_applications"] == 5
        assert stats["status_breakdown"]["applied"] == 2
        assert stats["status_breakdown"]["interviewing"] == 1
        assert stats["status_breakdown"]["rejected"] == 1
        assert stats["status_breakdown"]["offered"] == 1

    def test_get_applications_by_date_range(self, repo, db_session, test_user, test_job):
        """Test filtering applications by date range"""
        # Create applications with different dates
        app1 = Application(
            user_id=test_user.id,
            job_id=test_job.id,
            status="applied",
            created_at=datetime(2024, 1, 1)
        )
        app2 = Application(
            user_id=test_user.id,
            job_id=test_job.id,
            status="applied",
            created_at=datetime(2024, 1, 15)
        )
        app3 = Application(
            user_id=test_user.id,
            job_id=test_job.id,
            status="applied",
            created_at=datetime(2024, 2, 1)
        )
        db_session.add_all([app1, app2, app3])
        db_session.commit()

        # Act
        date_range_apps = repo.get_applications_by_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        # Assert
        assert len(date_range_apps) == 2
        assert all(app.created_at.date() >= date(2024, 1, 1) for app in date_range_apps)
        assert all(app.created_at.date() <= date(2024, 1, 31) for app in date_range_apps)
```

#### API Testing
```python
# backend/tests/test_auth_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token

class TestAuthAPI:
    @pytest.fixture
    async def client(self, app):
        """Test client"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    @pytest.fixture
    def test_user(self, db: Session):
        """Create test user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    async def test_login_success(self, client, test_user):
        """Test successful login"""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        # Arrange
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401

    async def test_register_success(self, client):
        """Test successful user registration"""
        # Arrange
        register_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=register_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data

    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        # Arrange
        register_data = {
            "email": "test@example.com",  # Existing email
            "password": "password123",
            "full_name": "Test User"
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=register_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_get_current_user(self, client, test_user):
        """Test getting current user with valid token"""
        # Arrange
        token = create_access_token({"sub": test_user.email})

        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    async def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        # Act
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == 401

    async def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        # Act
        response = await client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == 401
```

### Integration Testing Patterns

#### Database Integration Tests
```python
# backend/tests/integration/test_job_application_workflow.py
import pytest
from sqlalchemy.orm import Session
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.services.user_service import UserService
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

class TestJobApplicationWorkflow:
    """Integration tests for complete job application workflow"""

    @pytest.fixture
    def db_session(self):
        """Database session for integration tests"""
        # Setup real database session
        pass

    @pytest.fixture
    def user_service(self, db_session):
        return UserService(db_session)

    @pytest.fixture
    def job_service(self, db_session):
        return JobService(db_session)

    @pytest.fixture
    def application_service(self, db_session):
        return ApplicationService(db_session)

    def test_complete_application_workflow(self, user_service, job_service, application_service):
        """Test complete job application workflow"""
        # 1. Create user
        user_data = {
            "email": "applicant@example.com",
            "password": "password123",
            "full_name": "Test Applicant"
        }
        user = user_service.create_user(user_data)
        assert user.email == "applicant@example.com"

        # 2. Create job
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "description": "Great job opportunity",
            "location": "Remote",
            "salary_range": "$80k-$120k"
        }
        job = job_service.create_job(job_data)
        assert job.title == "Software Engineer"

        # 3. Create application
        application_data = {
            "job_id": job.id,
            "cover_letter": "I am very interested in this position...",
            "resume_url": "https://example.com/resume.pdf"
        }
        application = application_service.create_application(user.id, application_data)
        assert application.user_id == user.id
        assert application.job_id == job.id
        assert application.status == "applied"

        # 4. Update application status
        updated_application = application_service.update_application_status(
            application.id,
            "interviewing",
            "Passed initial screening"
        )
        assert updated_application.status == "interviewing"
        assert updated_application.notes == "Passed initial screening"

        # 5. Verify relationships
        user_applications = application_service.get_user_applications(user.id)
        assert len(user_applications) == 1
        assert user_applications[0].job.title == "Software Engineer"

        job_applications = application_service.get_job_applications(job.id)
        assert len(job_applications) == 1
        assert job_applications[0].user.email == "applicant@example.com"

    def test_application_status_transitions(self, user_service, job_service, application_service):
        """Test valid application status transitions"""
        # Setup
        user = user_service.create_user({
            "email": "transition@example.com",
            "password": "password123"
        })
        job = job_service.create_job({
            "title": "Test Job",
            "company": "Test Corp"
        })
        application = application_service.create_application(user.id, {"job_id": job.id})

        # Test valid transitions
        valid_transitions = [
            ("applied", "reviewing"),
            ("reviewing", "interviewing"),
            ("interviewing", "offered"),
            ("offered", "accepted"),
            ("interviewing", "rejected"),
            ("reviewing", "rejected")
        ]

        for from_status, to_status in valid_transitions:
            # Set initial status
            application_service.update_application_status(application.id, from_status)

            # Transition to new status
            updated = application_service.update_application_status(application.id, to_status)
            assert updated.status == to_status

    def test_application_search_and_filtering(self, user_service, job_service, application_service):
        """Test application search and filtering functionality"""
        # Create test data
        user1 = user_service.create_user({"email": "user1@example.com", "password": "pass"})
        user2 = user_service.create_user({"email": "user2@example.com", "password": "pass"})

        jobs = []
        for i in range(3):
            job = job_service.create_job({
                "title": f"Job {i}",
                "company": f"Company {i}",
                "location": "Remote" if i % 2 == 0 else "Office"
            })
            jobs.append(job)

        # Create applications
        applications = []
        statuses = ["applied", "interviewing", "offered", "rejected"]
        for i, job in enumerate(jobs):
            for j, user in enumerate([user1, user2]):
                app = application_service.create_application(user.id, {"job_id": job.id})
                application_service.update_application_status(app.id, statuses[(i + j) % len(statuses)])
                applications.append(app)

        # Test filtering by status
        applied_apps = application_service.get_applications_by_status("applied")
        assert len(applied_apps) >= 2

        # Test filtering by user
        user1_apps = application_service.get_user_applications(user1.id)
        assert len(user1_apps) == 3

        # Test filtering by date range
        from datetime import date, timedelta
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)

        recent_apps = application_service.get_applications_by_date_range(start_date, end_date)
        assert len(recent_apps) == len(applications)
```

#### Background Task Testing
```python
# backend/tests/integration/test_background_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from app.tasks.job_scraping_tasks import scrape_jobs_task
from app.tasks.analytics_tasks import update_analytics_task
from app.services.job_service import JobService
from app.services.analytics_service import AnalyticsService

class TestBackgroundTasks:
    """Integration tests for background tasks"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()

    @patch('app.tasks.job_scraping_tasks.JobScraper')
    def test_scrape_jobs_task_success(self, mock_scraper_class, mock_db_session):
        """Test successful job scraping task"""
        # Arrange
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        mock_scraper.scrape_source.return_value = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "Remote",
                "description": "Great job",
                "url": "https://example.com/job/1"
            }
        ]

        mock_service = MagicMock()
        with patch('app.tasks.job_scraping_tasks.JobService', return_value=mock_service):
            # Act
            result = scrape_jobs_task.apply(args=[["linkedin"]])

            # Assert
            assert result.state == "SUCCESS"
            assert result.result["total_processed"] == 1
            assert result.result["total_saved"] == 1
            mock_scraper.scrape_source.assert_called_once_with("linkedin")
            mock_service.create_job_from_scraped_data.assert_called_once()

    @patch('app.tasks.job_scraping_tasks.JobScraper')
    def test_scrape_jobs_task_failure_retry(self, mock_scraper_class, mock_db_session):
        """Test job scraping task failure and retry"""
        # Arrange
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_source.side_effect = Exception("Scraping failed")

        # Act
        result = scrape_jobs_task.apply(args=[["linkedin"]])

        # Assert
        assert result.state == "RETRY"
        # Task should be retried with exponential backoff

    def test_update_analytics_task(self, mock_db_session):
        """Test analytics update task"""
        # Arrange
        mock_service = MagicMock()
        with patch('app.tasks.analytics_tasks.AnalyticsService', return_value=mock_service):
            # Act
            result = update_analytics_task.apply()

            # Assert
            assert result.state == "SUCCESS"
            mock_service.update_user_analytics.assert_called_once()
            mock_service.update_job_analytics.assert_called_once()
            mock_service.update_application_analytics.assert_called_once()
```

## Frontend Testing

### Component Testing Patterns

#### React Component Testing
```typescript
// frontend/tests/components/DataTable.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DataTable } from '@/components/ui/DataTable';

interface TestData {
  id: number;
  name: string;
  email: string;
  status: string;
}

const mockData: TestData[] = [
  { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'active' },
];

const columns = [
  { key: 'name' as keyof TestData, header: 'Name', sortable: true },
  { key: 'email' as keyof TestData, header: 'Email', sortable: true },
  { key: 'status' as keyof TestData, header: 'Status' },
];

describe('DataTable', () => {
  it('renders table with data', () => {
    render(<DataTable data={mockData} columns={columns} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<DataTable data={[]} columns={columns} loading={true} />);

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('filters data based on search term', async () => {
    render(<DataTable data={mockData} columns={columns} searchable={true} />);

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
    });
  });

  it('sorts data when column header is clicked', () => {
    render(<DataTable data={mockData} columns={columns} />);

    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);

    // Check if data is sorted (this would depend on your sorting logic)
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Bob Johnson'); // Assuming ascending sort
  });

  it('calls onRowClick when row is clicked', () => {
    const mockOnRowClick = jest.fn();
    render(<DataTable data={mockData} columns={columns} onRowClick={mockOnRowClick} />);

    const firstRow = screen.getByText('John Doe').closest('tr');
    fireEvent.click(firstRow!);

    expect(mockOnRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  it('paginates data correctly', () => {
    render(<DataTable data={mockData} columns={columns} pageSize={2} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Johnson')).not.toBeInTheDocument();

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
  });

  it('shows pagination info correctly', () => {
    render(<DataTable data={mockData} columns={columns} pageSize={2} />);

    expect(screen.getByText('Showing 1 to 2 of 3 results')).toBeInTheDocument();
  });
});
```

#### Custom Hook Testing
```typescript
// frontend/tests/hooks/useApi.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi } from '@/hooks/useApi';

// Mock the API client
jest.mock('@/lib/api/client', () => ({
  fetchApi: jest.fn(),
}));

import { fetchApi } from '@/lib/api/client';

const mockFetchApi = fetchApi as jest.MockedFunction<typeof fetchApi>;

describe('useApi', () => {
  beforeEach(() => {
    mockFetchApi.mockClear();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useApi('/test-endpoint'));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should execute API call and handle success', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });

    expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params: undefined });
  });

  it('should handle API error', async () => {
    const errorMessage = 'API Error';
    mockFetchApi.mockResolvedValueOnce({ data: null, error: errorMessage });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toEqual(errorMessage);
    });
  });

  it('should execute immediately when immediate option is true', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    renderHook(() => useApi('/test-endpoint', { immediate: true }));

    await waitFor(() => {
      expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params: undefined });
    });
  });

  it('should call onSuccess callback when provided', async () => {
    const mockData = { id: 1, name: 'Test' };
    const onSuccess = jest.fn();
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() =>
      useApi('/test-endpoint', { onSuccess })
    );

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockData);
    });
  });

  it('should call onError callback when provided', async () => {
    const errorMessage = 'API Error';
    const onError = jest.fn();
    mockFetchApi.mockResolvedValueOnce({ data: null, error: errorMessage });

    const { result } = renderHook(() =>
      useApi('/test-endpoint', { onError })
    );

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(errorMessage);
    });
  });

  it('should pass params to API call', async () => {
    const mockData = { id: 1, name: 'Test' };
    const params = { page: 1, limit: 10 };
    mockFetchApi.mockResolvedValueOnce({ data: mockData, error: null });

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute(params);
    });

    await waitFor(() => {
      expect(mockFetchApi).toHaveBeenCalledWith('/test-endpoint', { params });
    });
  });

  it('should handle network errors', async () => {
    const networkError = new Error('Network error');
    mockFetchApi.mockRejectedValueOnce(networkError);

    const { result } = renderHook(() => useApi('/test-endpoint'));

    act(() => {
      result.current.execute();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toEqual('Network error');
    });
  });
});
```

### Form Testing Patterns

#### React Hook Form Testing
```typescript
// frontend/tests/components/forms/NewFeatureForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NewFeatureForm } from '@/components/forms/NewFeatureForm';

describe('NewFeatureForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText('Title *')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority *')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Add a tag')).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);

    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Test Feature' }
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Test description' }
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Test Feature',
        description: 'Test description',
        priority: 'medium',
        tags: []
      });
    });
  });

  it('handles tag addition and removal', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const tagInput = screen.getByPlaceholderText('Add a tag');
    const addButton = screen.getByRole('button', { name: 'Add' });

    fireEvent.change(tagInput, { target: { value: 'urgent' } });
    fireEvent.click(addButton);

    expect(screen.getByText('urgent ×')).toBeInTheDocument();

    fireEvent.click(screen.getByText('urgent ×'));
    expect(screen.queryByText('urgent ×')).not.toBeInTheDocument();
  });

  it('prevents adding duplicate tags', () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const tagInput = screen.getByPlaceholderText('Add a tag');
    const addButton = screen.getByRole('button', { name: 'Add' });

    fireEvent.change(tagInput, { target: { value: 'test' } });
    fireEvent.click(addButton);
    fireEvent.change(tagInput, { target: { value: 'test' } });
    fireEvent.click(addButton);

    expect(screen.getAllByText('test ×')).toHaveLength(1);
  });

  it('validates title length', async () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const longTitle = 'a'.repeat(101); // Exceeds max length
    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: longTitle }
    });

    fireEvent.click(screen.getByRole('button', { name: 'Create Feature' }));

    await waitFor(() => {
      expect(screen.getByText('Title must be less than 100 characters')).toBeInTheDocument();
    });
  });

  it('validates tag constraints', async () => {
    render(<NewFeatureForm onSubmit={mockOnSubmit} />);

    const tagInput = screen.getByPlaceholderText('Add a tag');
    const addButton = screen.getByRole('button', { name: 'Add' });

    // Add maximum allowed tags
    for (let i = 0; i < 5; i++) {
      fireEvent.change(tagInput, { target: { value: `tag${i}` } });
      fireEvent.click(addButton);
    }

    // Try to add one more
    fireEvent.change(tagInput, { target: { value: 'extra-tag' } });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Maximum 5 tags allowed')).toBeInTheDocument();
    });
  });
});
```

## End-to-End Testing

### Playwright E2E Tests

#### Authentication Flow Testing
```typescript
// frontend/tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should allow user to register and login', async ({ page }) => {
    // Go to registration page
    await page.goto('/register');

    // Fill registration form
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.fill('[data-testid="confirm-password-input"]', 'password123');

    // Submit form
    await page.click('[data-testid="register-button"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Logout
    await page.click('[data-testid="logout-button"]');

    // Should redirect to login
    await expect(page).toHaveURL('/login');

    // Login with new account
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
  });

  test('should redirect authenticated users away from login', async ({ page, context }) => {
    // Create authenticated context
    // ... authentication setup ...

    await page.goto('/login');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });
});
```

#### Job Application Workflow Testing
```typescript
// frontend/tests/e2e/job-application.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Job Application Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should allow user to browse and apply to jobs', async ({ page }) => {
    // Navigate to jobs page
    await page.goto('/jobs');

    // Search for jobs
    await page.fill('[data-testid="job-search-input"]', 'Software Engineer');
    await page.click('[data-testid="search-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="job-card"]');

    // Click on first job
    await page.click('[data-testid="job-card"]:first-child');

    // Should show job details
    await expect(page.locator('[data-testid="job-title"]')).toBeVisible();

    // Apply to job
    await page.click('[data-testid="apply-button"]');

    // Fill application form
    await page.fill('[data-testid="cover-letter"]', 'I am interested in this position...');
    await page.setInputFiles('[data-testid="resume-upload"]', 'test-resume.pdf');

    // Submit application
    await page.click('[data-testid="submit-application"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Application submitted');

    // Check applications page
    await page.goto('/applications');
    await expect(page.locator('[data-testid="application-card"]')).toBeVisible();
  });

  test('should allow user to track application status', async ({ page }) => {
    await page.goto('/applications');

    // Click on application
    await page.click('[data-testid="application-card"]:first-child');

    // Should show application details
    await expect(page.locator('[data-testid="application-status"]')).toBeVisible();

    // Update status (if admin/simulated)
    // ... status update logic ...

    // Check status change
    await page.reload();
    await expect(page.locator('[data-testid="application-status"]')).toContainText('Under Review');
  });

  test('should handle application form validation', async ({ page }) => {
    await page.goto('/jobs');
    await page.click('[data-testid="job-card"]:first-child');
    await page.click('[data-testid="apply-button"]');

    // Try to submit without required fields
    await page.click('[data-testid="submit-application"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Cover letter is required');

    // Fill required fields
    await page.fill('[data-testid="cover-letter"]', 'Test cover letter');

    // Submit should work now
    await page.click('[data-testid="submit-application"]');
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});
```

## Testing Infrastructure

### Test Configuration

#### Backend Test Configuration
```python
# backend/pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API tests
```

#### Frontend Test Configuration
```javascript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

### Test Fixtures and Utilities

#### Backend Test Fixtures
```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base, get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine, tables):
    """Create test database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_job(db_session: Session):
    """Create test job"""
    job = Job(
        title="Software Engineer",
        company="Test Corp",
        description="Test job description",
        location="Remote"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job

@pytest.fixture
def test_application(db_session: Session, test_user: User, test_job: Job):
    """Create test application"""
    application = Application(
        user_id=test_user.id,
        job_id=test_job.id,
        status="applied"
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application
```

#### Frontend Test Utilities
```typescript
// frontend/tests/utils/test-utils.tsx
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';

// Custom render function with providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );

  return render(ui, { wrapper, ...options });
};

// Mock API responses
export const mockApiResponse = (data: any, error?: string) => ({
  data,
  error,
  isLoading: false,
  isError: !!error,
});

// Mock user authentication
export const mockAuthenticatedUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  isActive: true,
};

// Generate test data
export const generateTestJobs = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    title: `Test Job ${i + 1}`,
    company: `Company ${i + 1}`,
    location: 'Remote',
    salary: `$${80 + i * 10}k - $${100 + i * 10}k`,
    description: `Test job description ${i + 1}`,
    createdAt: new Date().toISOString(),
  }));
};

export * from '@testing-library/react';
export { customRender as render };
```

### Test Data Management

#### Test Data Factory
```python
# backend/tests/factories.py
from faker import Faker
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

fake = Faker()

class UserFactory:
    @staticmethod
    def create(**overrides):
        defaults = {
            'email': fake.email(),
            'hashed_password': 'hashed_password',
            'full_name': fake.name(),
            'is_active': True,
        }
        defaults.update(overrides)
        return User(**defaults)

class JobFactory:
    @staticmethod
    def create(**overrides):
        defaults = {
            'title': fake.job(),
            'company': fake.company(),
            'description': fake.text(),
            'location': fake.city(),
            'salary_range': f"${fake.random_int(50, 100)}k-${fake.random_int(100, 200)}k",
            'job_type': fake.random_element(['full-time', 'part-time', 'contract']),
        }
        defaults.update(overrides)
        return Job(**defaults)

class ApplicationFactory:
    @staticmethod
    def create(user_id: int, job_id: int, **overrides):
        defaults = {
            'user_id': user_id,
            'job_id': job_id,
            'status': 'applied',
            'cover_letter': fake.text(),
        }
        defaults.update(overrides)
        return Application(**defaults)
```

### Continuous Integration Testing

#### GitHub Actions Test Workflow
```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend

  test-frontend:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info
        flags: frontend

  e2e-test:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install Playwright
      run: |
        cd frontend
        npx playwright install

    - name: Run E2E tests
      run: |
        cd frontend
        npx playwright test
```

## Testing Best Practices

### Test Organization
- **Unit Tests**: `tests/unit/` - Test individual functions/methods
- **Integration Tests**: `tests/integration/` - Test component interactions
- **E2E Tests**: `tests/e2e/` - Test complete user workflows
- **Fixtures**: `tests/fixtures/` - Reusable test data
- **Utils**: `tests/utils/` - Test utilities and helpers

### Naming Conventions
- **Test Files**: `test_*.py` (backend), `*.test.ts` (frontend)
- **Test Methods**: `test_*` with descriptive names
- **Mock Files**: `mock_*.py` or use `unittest.mock`

### Test Quality Guidelines
- **Coverage**: Aim for 80%+ code coverage
- **Isolation**: Each test should be independent
- **Readability**: Clear test names and documentation
- **Maintainability**: DRY principle, reusable fixtures
- **Performance**: Fast tests, parallel execution when possible

### Common Testing Patterns
- **Arrange-Act-Assert**: Clear test structure
- **Given-When-Then**: BDD-style test descriptions
- **Test Doubles**: Mocks, stubs, fakes, spies
- **Parameterized Tests**: Test multiple inputs with single test
- **Data-Driven Tests**: Test with various data sets

---

*See also: [[code-examples|Code Examples]], [[development-guide|Development Guide]], [[api-reference|API Reference]]*"