"""
Job Recommendation Test Framework

This module provides comprehensive testing for the job recommendation system including:
- Test user profiles for recommendation testing
- API client for job recommendation endpoints
- Recommendation relevance validation
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.app.core.database import get_db
from backend.app.models.job import Job
from backend.app.models.user import User
from backend.app.services.recommendation_engine import RecommendationEngine
from backend.app.services.enhanced_recommendation_service import enhanced_recommendation_service
from tests.e2e.base import BaseE2ETest


@dataclass
class TestUserProfile:
    """Test user profile for recommendation testing"""
    name: str
    email: str
    skills: List[str]
    preferred_locations: List[str]
    experience_level: str
    career_goals: List[str]
    salary_expectations: Optional[Dict[str, int]]
    expected_match_types: List[str]  # Types of jobs this user should match well with


@dataclass
class RecommendationTestResult:
    """Result of recommendation test execution"""
    success: bool
    user_id: int
    recommendations_count: int
    average_score: float
    high_quality_matches: int
    execution_time: float
    error_message: Optional[str]
    relevance_score: float
    validation_errors: List[str]


@dataclass
class RelevanceMetrics:
    """Metrics for evaluating recommendation relevance"""
    total_recommendations: int
    skill_matches: int
    location_matches: int
    experience_matches: int
    salary_matches: int
    overall_relevance_score: float
    quality_distribution: Dict[str, int]  # excellent, high, medium, low


class JobRecommendationTestFramework(BaseE2ETest):
    """
    Test framework for job recommendation functionality
    
    Provides methods to:
    - Create and manage test user profiles
    - Test recommendation API endpoints
    - Validate recommendation relevance and quality
    - Measure recommendation performance
    """
    
    def __init__(self):
        super().__init__()
        self.db: Session = next(get_db())
        self.test_users: List[User] = []
        self.test_jobs: List[Job] = []
        self.api_client = httpx.AsyncClient(base_url="http://localhost:8000")
        
        # Define test user profiles with different characteristics
        self.test_profiles = [
            TestUserProfile(
                name="Junior Python Developer",
                email="junior_python@test.com",
                skills=["Python", "Django", "PostgreSQL", "Git"],
                preferred_locations=["San Francisco", "Remote"],
                experience_level="junior",
                career_goals=["Backend Development", "Full Stack"],
                salary_expectations={"min": 70000, "max": 90000},
                expected_match_types=["junior", "entry-level", "python"]
            ),
            TestUserProfile(
                name="Senior Full Stack Engineer",
                email="senior_fullstack@test.com",
                skills=["React", "Node.js", "TypeScript", "AWS", "Docker", "Kubernetes"],
                preferred_locations=["New York", "Austin", "Remote"],
                experience_level="senior",
                career_goals=["Technical Leadership", "Architecture"],
                salary_expectations={"min": 130000, "max": 180000},
                expected_match_types=["senior", "lead", "full-stack", "react"]
            ),
            TestUserProfile(
                name="Data Scientist",
                email="data_scientist@test.com",
                skills=["Python", "Machine Learning", "TensorFlow", "Pandas", "SQL"],
                preferred_locations=["Seattle", "Boston", "Remote"],
                experience_level="mid",
                career_goals=["Machine Learning", "AI Research"],
                salary_expectations={"min": 110000, "max": 150000},
                expected_match_types=["data", "ml", "python", "analytics"]
            ),
            TestUserProfile(
                name="DevOps Engineer",
                email="devops_engineer@test.com",
                skills=["AWS", "Terraform", "Kubernetes", "Docker", "Jenkins", "Python"],
                preferred_locations=["Remote"],
                experience_level="mid",
                career_goals=["Cloud Architecture", "Infrastructure"],
                salary_expectations={"min": 100000, "max": 140000},
                expected_match_types=["devops", "cloud", "infrastructure", "aws"]
            ),
            TestUserProfile(
                name="Frontend Specialist",
                email="frontend_specialist@test.com",
                skills=["React", "Vue.js", "JavaScript", "CSS", "HTML", "Figma"],
                preferred_locations=["Los Angeles", "San Diego"],
                experience_level="mid",
                career_goals=["UI/UX", "Frontend Architecture"],
                salary_expectations={"min": 90000, "max": 120000},
                expected_match_types=["frontend", "react", "javascript", "ui"]
            )
        ]
    
    async def setup_test_environment(self) -> bool:
        """
        Set up test environment with test users and sample jobs
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create test users from profiles
            await self._create_test_users()
            
            # Create sample jobs for testing
            await self._create_sample_jobs()
            
            self.logger.info(f"Test environment setup complete. Created {len(self.test_users)} users and {len(self.test_jobs)} jobs")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def _create_test_users(self) -> None:
        """Create test users from predefined profiles"""
        for profile in self.test_profiles:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == profile.email
            ).first()
            
            if existing_user:
                self.test_users.append(existing_user)
                continue
            
            # Create new test user
            user = User(
                email=profile.email,
                name=profile.name,
                skills=profile.skills,
                preferred_locations=profile.preferred_locations,
                experience_level=profile.experience_level,
                career_goals=profile.career_goals,
                salary_expectations=profile.salary_expectations,
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            self.test_users.append(user)
            
            self.logger.info(f"Created test user: {profile.name} (ID: {user.id})")
    
    async def _create_sample_jobs(self) -> None:
        """Create sample jobs that should match different user profiles"""
        sample_jobs = [
            # Jobs for Junior Python Developer
            {
                "title": "Junior Python Developer",
                "company": "TechStart Inc",
                "location": "San Francisco, CA",
                "description": "Entry-level Python developer position with Django framework",
                "tech_stack": ["Python", "Django", "PostgreSQL", "Git"],
                "salary_range": "$70,000 - $85,000",
                "job_type": "full-time",
                "remote_option": False,
                "experience_required": "0-2 years"
            },
            {
                "title": "Backend Developer - Python",
                "company": "Remote First Co",
                "location": "Remote",
                "description": "Remote Python backend developer with FastAPI experience",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "salary_range": "$75,000 - $90,000",
                "job_type": "full-time",
                "remote_option": True,
                "experience_required": "1-3 years"
            },
            
            # Jobs for Senior Full Stack Engineer
            {
                "title": "Senior Full Stack Engineer",
                "company": "Enterprise Solutions",
                "location": "New York, NY",
                "description": "Lead full stack development with React and Node.js",
                "tech_stack": ["React", "Node.js", "TypeScript", "AWS", "Docker"],
                "salary_range": "$140,000 - $170,000",
                "job_type": "full-time",
                "remote_option": False,
                "experience_required": "5+ years"
            },
            {
                "title": "Technical Lead - Full Stack",
                "company": "Innovation Labs",
                "location": "Austin, TX",
                "description": "Technical leadership role for full stack development team",
                "tech_stack": ["React", "Node.js", "TypeScript", "Kubernetes", "AWS"],
                "salary_range": "$150,000 - $180,000",
                "job_type": "full-time",
                "remote_option": True,
                "experience_required": "6+ years"
            },
            
            # Jobs for Data Scientist
            {
                "title": "Data Scientist - ML",
                "company": "AI Research Corp",
                "location": "Seattle, WA",
                "description": "Machine learning and data analysis position",
                "tech_stack": ["Python", "TensorFlow", "Pandas", "SQL", "AWS"],
                "salary_range": "$120,000 - $145,000",
                "job_type": "full-time",
                "remote_option": True,
                "experience_required": "3-5 years"
            },
            {
                "title": "Senior Data Analyst",
                "company": "Data Insights Inc",
                "location": "Boston, MA",
                "description": "Advanced analytics and machine learning implementation",
                "tech_stack": ["Python", "Machine Learning", "SQL", "Tableau"],
                "salary_range": "$110,000 - $140,000",
                "job_type": "full-time",
                "remote_option": False,
                "experience_required": "4+ years"
            },
            
            # Jobs for DevOps Engineer
            {
                "title": "DevOps Engineer - Cloud",
                "company": "Cloud Native Systems",
                "location": "Remote",
                "description": "Cloud infrastructure and DevOps automation",
                "tech_stack": ["AWS", "Terraform", "Kubernetes", "Docker", "Jenkins"],
                "salary_range": "$110,000 - $135,000",
                "job_type": "full-time",
                "remote_option": True,
                "experience_required": "3-5 years"
            },
            {
                "title": "Infrastructure Engineer",
                "company": "ScaleUp Tech",
                "location": "Remote",
                "description": "Infrastructure automation and cloud architecture",
                "tech_stack": ["AWS", "Terraform", "Python", "Kubernetes"],
                "salary_range": "$105,000 - $130,000",
                "job_type": "full-time",
                "remote_option": True,
                "experience_required": "3+ years"
            },
            
            # Jobs for Frontend Specialist
            {
                "title": "Frontend Developer - React",
                "company": "UI/UX Studio",
                "location": "Los Angeles, CA",
                "description": "Frontend development with modern React and design systems",
                "tech_stack": ["React", "JavaScript", "CSS", "Figma", "TypeScript"],
                "salary_range": "$95,000 - $115,000",
                "job_type": "full-time",
                "remote_option": False,
                "experience_required": "2-4 years"
            },
            {
                "title": "UI Developer",
                "company": "Design Forward",
                "location": "San Diego, CA",
                "description": "User interface development with Vue.js and modern CSS",
                "tech_stack": ["Vue.js", "JavaScript", "CSS", "HTML", "Sass"],
                "salary_range": "$90,000 - $110,000",
                "job_type": "full-time",
                "remote_option": False,
                "experience_required": "2-5 years"
            }
        ]
        
        # Create jobs for each test user
        for user in self.test_users:
            for job_data in sample_jobs:
                job = Job(
                    user_id=user.id,
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    tech_stack=job_data["tech_stack"],
                    salary_range=job_data["salary_range"],
                    job_type=job_data["job_type"],
                    remote_option=job_data["remote_option"],
                    status="not_applied",
                    source="test_framework",
                    link=f"https://example.com/job/{job_data['title'].lower().replace(' ', '-')}",
                    created_at=datetime.now()
                )
                
                self.db.add(job)
                self.test_jobs.append(job)
        
        self.db.commit()
        self.logger.info(f"Created {len(self.test_jobs)} sample jobs for testing")
    
    async def test_recommendation_api_endpoints(self) -> Dict[str, Any]:
        """
        Test job recommendation API endpoints
        
        Returns:
            Dict containing test results for all endpoints
        """
        results = {
            "basic_recommendations": [],
            "enhanced_recommendations": [],
            "job_analysis": [],
            "recommendation_insights": [],
            "api_performance": {}
        }
        
        try:
            for user in self.test_users:
                # Test basic recommendations endpoint
                basic_result = await self._test_basic_recommendations_api(user)
                results["basic_recommendations"].append(basic_result)
                
                # Test enhanced recommendations endpoint
                enhanced_result = await self._test_enhanced_recommendations_api(user)
                results["enhanced_recommendations"].append(enhanced_result)
                
                # Test job analysis endpoint (if we have jobs)
                if self.test_jobs:
                    analysis_result = await self._test_job_analysis_api(user, self.test_jobs[0])
                    results["job_analysis"].append(analysis_result)
                
                # Test recommendation insights endpoint
                insights_result = await self._test_recommendation_insights_api(user)
                results["recommendation_insights"].append(insights_result)
            
            # Calculate overall API performance metrics
            results["api_performance"] = self._calculate_api_performance_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing recommendation API endpoints: {e}")
            return {"error": str(e)}
    
    async def _test_basic_recommendations_api(self, user: User) -> Dict[str, Any]:
        """Test basic recommendations API endpoint"""
        start_time = time.time()
        
        try:
            # Create authentication headers (mock for testing)
            headers = {"Authorization": f"Bearer test_token_{user.id}"}
            
            # Test recommendations endpoint using RecommendationEngine directly
            recommendation_engine = RecommendationEngine(self.db)
            recommendations = recommendation_engine.get_recommendations(user, limit=10)
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": True,
                "recommendations_count": len(recommendations),
                "execution_time": execution_time,
                "average_score": sum(r["score"] for r in recommendations) / len(recommendations) if recommendations else 0,
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": False,
                "recommendations_count": 0,
                "execution_time": execution_time,
                "average_score": 0,
                "error_message": str(e)
            }
    
    async def _test_enhanced_recommendations_api(self, user: User) -> Dict[str, Any]:
        """Test enhanced recommendations API endpoint"""
        start_time = time.time()
        
        try:
            # Test enhanced recommendations using service directly
            recommendations = enhanced_recommendation_service.get_personalized_recommendations(
                db=self.db,
                user_id=user.id,
                limit=10,
                min_score=0.3
            )
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": True,
                "recommendations_count": len(recommendations),
                "execution_time": execution_time,
                "average_score": sum(r.get("overall_score", 0) for r in recommendations) / len(recommendations) if recommendations else 0,
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": False,
                "recommendations_count": 0,
                "execution_time": execution_time,
                "average_score": 0,
                "error_message": str(e)
            }
    
    async def _test_job_analysis_api(self, user: User, job: Job) -> Dict[str, Any]:
        """Test job analysis API endpoint"""
        start_time = time.time()
        
        try:
            # Test job analysis using enhanced recommendation service
            analysis = enhanced_recommendation_service.generate_enhanced_recommendation(
                db=self.db,
                user_id=user.id,
                job=job
            )
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "job_id": job.id,
                "success": True,
                "analysis_generated": analysis is not None,
                "execution_time": execution_time,
                "overall_score": analysis.get("overall_score", 0) if analysis else 0,
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "job_id": job.id,
                "success": False,
                "analysis_generated": False,
                "execution_time": execution_time,
                "overall_score": 0,
                "error_message": str(e)
            }
    
    async def _test_recommendation_insights_api(self, user: User) -> Dict[str, Any]:
        """Test recommendation insights API endpoint"""
        start_time = time.time()
        
        try:
            # Get recommendations for insights analysis
            recommendations = enhanced_recommendation_service.get_personalized_recommendations(
                db=self.db,
                user_id=user.id,
                limit=20,
                min_score=0.0
            )
            
            # Generate mock insights based on recommendations
            insights = {
                "profile_completeness": 0.8,
                "average_match_score": sum(r.get("overall_score", 0) for r in recommendations) / len(recommendations) if recommendations else 0,
                "recommendations_analyzed": len(recommendations),
                "market_competitiveness": "Competitive" if len(recommendations) > 5 else "Developing"
            }
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "success": True,
                "insights_generated": True,
                "execution_time": execution_time,
                "profile_completeness": insights["profile_completeness"],
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "success": False,
                "insights_generated": False,
                "execution_time": execution_time,
                "profile_completeness": 0,
                "error_message": str(e)
            }
    
    def validate_recommendation_relevance(self, user: User, recommendations: List[Dict[str, Any]]) -> RelevanceMetrics:
        """
        Validate the relevance of recommendations for a specific user
        
        Args:
            user: User to validate recommendations for
            recommendations: List of recommendation results
            
        Returns:
            RelevanceMetrics with detailed relevance analysis
        """
        if not recommendations:
            return RelevanceMetrics(
                total_recommendations=0,
                skill_matches=0,
                location_matches=0,
                experience_matches=0,
                salary_matches=0,
                overall_relevance_score=0.0,
                quality_distribution={"excellent": 0, "high": 0, "medium": 0, "low": 0}
            )
        
        skill_matches = 0
        location_matches = 0
        experience_matches = 0
        salary_matches = 0
        quality_distribution = {"excellent": 0, "high": 0, "medium": 0, "low": 0}
        
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        user_exp_level = user.experience_level.lower() if user.experience_level else ""
        
        for rec in recommendations:
            job_data = rec.get("job", {})
            overall_score = rec.get("overall_score", rec.get("score", 0))
            
            # Check skill matches
            job_tech_stack = job_data.get("tech_stack", [])
            if job_tech_stack:
                job_skills = set(s.lower() for s in job_tech_stack)
                if user_skills.intersection(job_skills):
                    skill_matches += 1
            
            # Check location matches
            job_location = job_data.get("location", "").lower()
            if job_location:
                if ("remote" in user_locations and "remote" in job_location) or \
                   any(loc in job_location for loc in user_locations):
                    location_matches += 1
            
            # Check experience level matches
            job_title = job_data.get("title", "").lower()
            if user_exp_level in job_title or \
               (user_exp_level == "junior" and any(term in job_title for term in ["junior", "entry", "associate"])) or \
               (user_exp_level == "senior" and any(term in job_title for term in ["senior", "lead", "principal"])):
                experience_matches += 1
            
            # Check salary matches (simplified)
            salary_range = job_data.get("salary_range", "")
            if salary_range and user.salary_expectations:
                # This is a simplified check - in practice, you'd parse the salary range
                salary_matches += 1
            
            # Categorize by quality
            if overall_score >= 0.8:
                quality_distribution["excellent"] += 1
            elif overall_score >= 0.6:
                quality_distribution["high"] += 1
            elif overall_score >= 0.4:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        total_recs = len(recommendations)
        overall_relevance_score = (
            (skill_matches / total_recs * 0.4) +
            (location_matches / total_recs * 0.3) +
            (experience_matches / total_recs * 0.2) +
            (salary_matches / total_recs * 0.1)
        )
        
        return RelevanceMetrics(
            total_recommendations=total_recs,
            skill_matches=skill_matches,
            location_matches=location_matches,
            experience_matches=experience_matches,
            salary_matches=salary_matches,
            overall_relevance_score=overall_relevance_score,
            quality_distribution=quality_distribution
        )
    
    def _calculate_api_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall API performance metrics"""
        all_results = []
        
        # Collect all API test results
        for endpoint_results in results.values():
            if isinstance(endpoint_results, list):
                all_results.extend(endpoint_results)
        
        if not all_results:
            return {"error": "No API results to analyze"}
        
        successful_calls = [r for r in all_results if r.get("success", False)]
        failed_calls = [r for r in all_results if not r.get("success", False)]
        
        execution_times = [r.get("execution_time", 0) for r in successful_calls]
        
        return {
            "total_api_calls": len(all_results),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "success_rate": len(successful_calls) / len(all_results) if all_results else 0,
            "average_response_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "max_response_time": max(execution_times) if execution_times else 0,
            "min_response_time": min(execution_times) if execution_times else 0
        }
    
    async def run_comprehensive_recommendation_test(self) -> Dict[str, Any]:
        """
        Run comprehensive job recommendation testing
        
        Returns:
            Dict containing complete test results
        """
        start_time = time.time()
        
        try:
            # Setup test environment
            setup_success = await self.setup_test_environment()
            if not setup_success:
                return {"error": "Failed to setup test environment"}
            
            # Test API endpoints
            api_results = await self.test_recommendation_api_endpoints()
            
            # Test recommendation relevance for each user
            relevance_results = []
            for user in self.test_users:
                try:
                    # Get recommendations using basic engine
                    recommendation_engine = RecommendationEngine(self.db)
                    recommendations = recommendation_engine.get_recommendations(user, limit=10)
                    
                    # Validate relevance
                    relevance_metrics = self.validate_recommendation_relevance(user, recommendations)
                    
                    relevance_results.append({
                        "user_id": user.id,
                        "user_name": user.name,
                        "relevance_metrics": relevance_metrics
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error testing relevance for user {user.id}: {e}")
                    relevance_results.append({
                        "user_id": user.id,
                        "user_name": user.name,
                        "error": str(e)
                    })
            
            total_execution_time = time.time() - start_time
            
            return {
                "test_summary": {
                    "total_execution_time": total_execution_time,
                    "test_users_created": len(self.test_users),
                    "test_jobs_created": len(self.test_jobs),
                    "timestamp": datetime.now().isoformat()
                },
                "api_test_results": api_results,
                "relevance_test_results": relevance_results,
                "overall_success": len([r for r in relevance_results if "error" not in r]) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive recommendation test: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup_test_environment(self) -> bool:
        """
        Clean up test environment by removing test data
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            # Remove test jobs
            for job in self.test_jobs:
                self.db.delete(job)
            
            # Remove test users
            for user in self.test_users:
                self.db.delete(user)
            
            self.db.commit()
            
            # Close API client
            await self.api_client.aclose()
            
            self.logger.info("Test environment cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during test environment cleanup: {e}")
            return False


# Convenience function for running the test
async def run_job_recommendation_test() -> Dict[str, Any]:
    """
    Convenience function to run job recommendation testing
    
    Returns:
        Dict containing test results
    """
    framework = JobRecommendationTestFramework()
    try:
        results = await framework.run_comprehensive_recommendation_test()
        return results
    finally:
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run the test when executed directly
    import asyncio
    
    async def main():
        results = await run_job_recommendation_test()
        print("Job Recommendation Test Results:")
        print("=" * 50)
        
        if "error" in results:
            print(f"Test failed with error: {results['error']}")
            return
        
        # Print summary
        summary = results.get("test_summary", {})
        print(f"Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
        print(f"Test users created: {summary.get('test_users_created', 0)}")
        print(f"Test jobs created: {summary.get('test_jobs_created', 0)}")
        print(f"Overall success: {results.get('overall_success', False)}")
        
        # Print API performance
        api_results = results.get("api_test_results", {})
        api_performance = api_results.get("api_performance", {})
        if api_performance:
            print(f"\nAPI Performance:")
            print(f"  Success rate: {api_performance.get('success_rate', 0):.2%}")
            print(f"  Average response time: {api_performance.get('average_response_time', 0):.3f}s")
        
        # Print relevance results summary
        relevance_results = results.get("relevance_test_results", [])
        if relevance_results:
            print(f"\nRelevance Test Results:")
            for result in relevance_results:
                if "error" not in result:
                    metrics = result.get("relevance_metrics", {})
                    print(f"  {result['user_name']}: {metrics.overall_relevance_score:.2%} relevance")
    
    asyncio.run(main())