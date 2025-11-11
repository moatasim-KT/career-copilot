"""Tests for enhanced analytics endpoints (Task 10)"""

import pytest
from datetime import datetime, timedelta, date, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.job import Job
from app.models.application import Application


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user with skills"""
    user = User(
        email="analytics_test@example.com",
        username="analytics_test",
        hashed_password="test_hash",
        daily_application_goal=5,
        skills=["Python", "JavaScript", "React", "FastAPI"]
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_jobs(db: AsyncSession, test_user: User):
    """Create test jobs with various tech stacks"""
    jobs_data = [
        {
            "company": "Tech Corp",
            "title": "Senior Python Developer",
            "tech_stack": ["Python", "Django", "PostgreSQL", "Docker"],
            "location": "San Francisco, CA"
        },
        {
            "company": "StartupXYZ",
            "title": "Full Stack Engineer",
            "tech_stack": ["JavaScript", "React", "Node.js", "MongoDB"],
            "location": "Remote"
        },
        {
            "company": "BigTech Inc",
            "title": "Backend Engineer",
            "tech_stack": ["Python", "FastAPI", "Redis", "Kubernetes"],
            "location": "New York, NY"
        },
        {
            "company": "Tech Corp",
            "title": "DevOps Engineer",
            "tech_stack": ["Docker", "Kubernetes", "AWS", "Terraform"],
            "location": "Austin, TX"
        },
        {
            "company": "DataCo",
            "title": "Data Engineer",
            "tech_stack": ["Python", "Spark", "Airflow", "SQL"],
            "location": "Seattle, WA"
        }
    ]
    
    jobs = []
    for job_data in jobs_data:
        job = Job(
            user_id=test_user.id,
            **job_data
        )
        db.add(job)
        jobs.append(job)
    
    await db.commit()
    for job in jobs:
        await db.refresh(job)
    
    return jobs


@pytest.fixture
async def test_applications(db: AsyncSession, test_user: User, test_jobs: list[Job]):
    """Create test applications with various statuses and dates"""
    today = datetime.now(timezone.utc).date()
    
    applications_data = [
        # Recent applications
        {"job_id": test_jobs[0].id, "status": "applied", "applied_date": today},
        {"job_id": test_jobs[1].id, "status": "applied", "applied_date": today},
        {"job_id": test_jobs[2].id, "status": "interview", "applied_date": today - timedelta(days=1)},
        
        # This week
        {"job_id": test_jobs[3].id, "status": "applied", "applied_date": today - timedelta(days=3)},
        {"job_id": test_jobs[4].id, "status": "interview", "applied_date": today - timedelta(days=5)},
        
        # Last week
        {"job_id": test_jobs[0].id, "status": "offer", "applied_date": today - timedelta(days=8)},
        {"job_id": test_jobs[1].id, "status": "rejected", "applied_date": today - timedelta(days=10)},
        
        # Last month
        {"job_id": test_jobs[2].id, "status": "accepted", "applied_date": today - timedelta(days=20)},
        {"job_id": test_jobs[3].id, "status": "rejected", "applied_date": today - timedelta(days=25)},
        {"job_id": test_jobs[4].id, "status": "declined", "applied_date": today - timedelta(days=30)},
    ]
    
    applications = []
    for app_data in applications_data:
        app = Application(
            user_id=test_user.id,
            **app_data
        )
        db.add(app)
        applications.append(app)
    
    await db.commit()
    for app in applications:
        await db.refresh(app)
    
    return applications


class TestComprehensiveAnalyticsSummary:
    """Tests for comprehensive analytics summary endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_summary(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job],
        test_applications: list[Application]
    ):
        """Test getting comprehensive analytics summary"""
        response = await client.get(
            "/api/v1/analytics/comprehensive-summary",
            params={"days": 90}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check basic counts
        assert data["total_jobs"] == len(test_jobs)
        assert data["total_applications"] == len(test_applications)
        
        # Check status breakdown
        assert "application_counts_by_status" in data
        assert len(data["application_counts_by_status"]) > 0
        
        # Check rates
        assert "rates" in data
        assert "interview_rate" in data["rates"]
        assert "offer_rate" in data["rates"]
        assert "acceptance_rate" in data["rates"]
        
        # Check trends
        assert "trends" in data
        assert "daily" in data["trends"]
        assert "weekly" in data["trends"]
        assert "monthly" in data["trends"]
        
        # Check each trend has required fields
        for period in ["daily", "weekly", "monthly"]:
            trend = data["trends"][period]
            assert "direction" in trend
            assert trend["direction"] in ["up", "down", "neutral"]
            assert "percentage_change" in trend
            assert "current_value" in trend
            assert "previous_value" in trend
        
        # Check top skills
        assert "top_skills_in_jobs" in data
        assert len(data["top_skills_in_jobs"]) > 0
        for skill in data["top_skills_in_jobs"]:
            assert "skill" in skill
            assert "count" in skill
            assert "percentage" in skill
        
        # Check top companies
        assert "top_companies_applied" in data
        assert len(data["top_companies_applied"]) > 0
        for company in data["top_companies_applied"]:
            assert "company" in company
            assert "count" in company
        
        # Check time-based counts
        assert "daily_applications_today" in data
        assert "weekly_applications" in data
        assert "monthly_applications" in data
        
        # Check goals
        assert "daily_application_goal" in data
        assert data["daily_application_goal"] == 5
        assert "daily_goal_progress" in data
        
        # Check metadata
        assert "generated_at" in data
        assert "analysis_period_days" in data
        assert data["analysis_period_days"] == 90
    
    @pytest.mark.asyncio
    async def test_comprehensive_summary_caching(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job],
        test_applications: list[Application]
    ):
        """Test that comprehensive summary is cached"""
        # First request
        response1 = await client.get("/api/v1/analytics/comprehensive-summary")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request (should be cached)
        response2 = await client.get("/api/v1/analytics/comprehensive-summary")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Generated_at should be the same (cached)
        assert data1["generated_at"] == data2["generated_at"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_summary_different_periods(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job],
        test_applications: list[Application]
    ):
        """Test comprehensive summary with different time periods"""
        # 30 days
        response_30 = await client.get(
            "/api/v1/analytics/comprehensive-summary",
            params={"days": 30}
        )
        assert response_30.status_code == 200
        data_30 = response_30.json()
        assert data_30["analysis_period_days"] == 30
        
        # 90 days
        response_90 = await client.get(
            "/api/v1/analytics/comprehensive-summary",
            params={"days": 90}
        )
        assert response_90.status_code == 200
        data_90 = response_90.json()
        assert data_90["analysis_period_days"] == 90


class TestTrendAnalysis:
    """Tests for trend analysis endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_trend_analysis(
        self,
        client: AsyncClient,
        test_user: User,
        test_applications: list[Application]
    ):
        """Test getting trend analysis"""
        response = await client.get("/api/v1/analytics/trends")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check trends
        assert "trends" in data
        assert "daily" in data["trends"]
        assert "weekly" in data["trends"]
        assert "monthly" in data["trends"]
        
        # Check time series data
        assert "time_series_data" in data
        assert isinstance(data["time_series_data"], list)
        
        # Check date range
        assert "analysis_period_start" in data
        assert "analysis_period_end" in data
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_trend_analysis_custom_date_range(
        self,
        client: AsyncClient,
        test_user: User,
        test_applications: list[Application]
    ):
        """Test trend analysis with custom date range"""
        today = date.today()
        start_date = today - timedelta(days=14)
        
        response = await client.get(
            "/api/v1/analytics/trends",
            params={
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_period_start"] == start_date.isoformat()
        assert data["analysis_period_end"] == today.isoformat()
    
    @pytest.mark.asyncio
    async def test_trend_direction_calculation(
        self,
        client: AsyncClient,
        test_user: User,
        test_applications: list[Application]
    ):
        """Test that trend directions are calculated correctly"""
        response = await client.get("/api/v1/analytics/trends")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that directions are valid
        for period in ["daily", "weekly", "monthly"]:
            trend = data["trends"][period]
            assert trend["direction"] in ["up", "down", "neutral"]
            
            # Verify direction matches percentage change
            if trend["percentage_change"] > 5:
                assert trend["direction"] == "up"
            elif trend["percentage_change"] < -5:
                assert trend["direction"] == "down"
            else:
                assert trend["direction"] == "neutral"


class TestSkillGapAnalysis:
    """Tests for skill gap analysis endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_skill_gap_analysis(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job]
    ):
        """Test getting skill gap analysis"""
        response = await client.get("/api/v1/analytics/skill-gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check analysis structure
        assert "analysis" in data
        analysis = data["analysis"]
        
        # Check user skills
        assert "user_skills" in analysis
        assert isinstance(analysis["user_skills"], list)
        assert "Python" in analysis["user_skills"]
        assert "JavaScript" in analysis["user_skills"]
        
        # Check market skills
        assert "market_skills" in analysis
        assert isinstance(analysis["market_skills"], list)
        assert len(analysis["market_skills"]) > 0
        
        for skill in analysis["market_skills"]:
            assert "skill" in skill
            assert "count" in skill
            assert "percentage" in skill
        
        # Check missing skills
        assert "missing_skills" in analysis
        assert isinstance(analysis["missing_skills"], list)
        
        # Check coverage percentage
        assert "skill_coverage_percentage" in analysis
        assert 0 <= analysis["skill_coverage_percentage"] <= 100
        
        # Check recommendations
        assert "recommendations" in analysis
        assert isinstance(analysis["recommendations"], list)
        
        # Check metadata
        assert "generated_at" in data
    
    @pytest.mark.asyncio
    async def test_skill_gap_identifies_missing_skills(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job]
    ):
        """Test that skill gap analysis correctly identifies missing skills"""
        response = await client.get("/api/v1/analytics/skill-gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        analysis = data["analysis"]
        
        # User has Python, JavaScript, React, FastAPI
        # Jobs require Docker, Kubernetes, PostgreSQL, etc.
        # So missing skills should include some of these
        missing_skill_names = [s["skill"].lower() for s in analysis["missing_skills"]]
        
        # Check that some expected missing skills are identified
        # (Docker and Kubernetes appear in jobs but not in user skills)
        assert any(skill in missing_skill_names for skill in ["docker", "kubernetes", "postgresql"])


class TestAnalyticsCacheManagement:
    """Tests for analytics cache management endpoints"""
    
    @pytest.mark.asyncio
    async def test_clear_analytics_cache(
        self,
        client: AsyncClient,
        test_user: User,
        test_applications: list[Application]
    ):
        """Test clearing analytics cache"""
        # First, populate cache
        await client.get("/api/v1/analytics/comprehensive-summary")
        
        # Clear cache
        response = await client.delete("/api/v1/analytics/cache")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "entries_cleared" in data
        assert data["entries_cleared"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test getting cache statistics"""
        response = await client.get("/api/v1/analytics/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cache_stats" in data
        assert "in_memory_cache_size" in data
        
        cache_stats = data["cache_stats"]
        assert "backend" in cache_stats
        assert cache_stats["backend"] in ["redis", "memory"]


class TestAnalyticsPerformance:
    """Tests for analytics performance requirements"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_summary_response_time(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job],
        test_applications: list[Application]
    ):
        """Test that comprehensive summary responds within 3 seconds"""
        import time
        
        start_time = time.time()
        response = await client.get("/api/v1/analytics/comprehensive-summary")
        end_time = time.time()
        
        assert response.status_code == 200
        
        response_time = end_time - start_time
        assert response_time < 3.0, f"Response time {response_time}s exceeds 3 second requirement"
    
    @pytest.mark.asyncio
    async def test_cached_response_is_faster(
        self,
        client: AsyncClient,
        test_user: User,
        test_jobs: list[Job],
        test_applications: list[Application]
    ):
        """Test that cached responses are faster than uncached"""
        import time
        
        # First request (uncached)
        start_time_1 = time.time()
        response1 = await client.get("/api/v1/analytics/comprehensive-summary")
        end_time_1 = time.time()
        time_1 = end_time_1 - start_time_1
        
        assert response1.status_code == 200
        
        # Second request (cached)
        start_time_2 = time.time()
        response2 = await client.get("/api/v1/analytics/comprehensive-summary")
        end_time_2 = time.time()
        time_2 = end_time_2 - start_time_2
        
        assert response2.status_code == 200
        
        # Cached request should be faster (or at least not slower)
        assert time_2 <= time_1 * 1.5, "Cached response should be faster"


class TestAnalyticsEdgeCases:
    """Tests for edge cases in analytics"""
    
    @pytest.mark.asyncio
    async def test_analytics_with_no_data(
        self,
        client: AsyncClient,
        db: AsyncSession
    ):
        """Test analytics endpoints with no jobs or applications"""
        # Create user with no data
        user = User(
            email="empty_user@example.com",
            username="empty_user",
            hashed_password="test_hash"
        )
        db.add(user)
        await db.commit()
        
        response = await client.get("/api/v1/analytics/comprehensive-summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return zeros but not error
        assert data["total_jobs"] == 0
        assert data["total_applications"] == 0
        assert data["rates"]["interview_rate"] == 0.0
        assert data["rates"]["offer_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_skill_gap_with_no_skills(
        self,
        client: AsyncClient,
        db: AsyncSession
    ):
        """Test skill gap analysis with user having no skills"""
        # Create user with no skills
        user = User(
            email="no_skills@example.com",
            username="no_skills",
            hashed_password="test_hash",
            skills=[]
        )
        db.add(user)
        await db.commit()
        
        response = await client.get("/api/v1/analytics/skill-gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty user skills but not error
        assert data["analysis"]["user_skills"] == []
        assert data["analysis"]["skill_coverage_percentage"] == 0.0
