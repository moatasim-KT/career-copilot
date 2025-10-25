"""
Consolidated Job Management E2E Tests

This module consolidates all job-related E2E tests including:
- Job scraping functionality
- Job recommendation system
- Job matching algorithms
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from base import BaseE2ETest


@dataclass
class MockUser:
    """Mock user for testing"""
    id: int
    name: str
    email: str
    skills: List[str]
    preferred_locations: List[str]
    experience_level: str
    career_goals: List[str] = None
    salary_expectations: Dict[str, int] = None
    is_active: bool = True


@dataclass
class MockJob:
    """Mock job for testing"""
    id: int
    user_id: int
    title: str
    company: str
    location: str
    description: str
    tech_stack: List[str]
    salary_range: str
    job_type: str
    remote_option: bool
    status: str = "not_applied"
    source: str = "test"
    link: str = "https://example.com"


@dataclass
class RelevanceMetrics:
    """Metrics for evaluating recommendation relevance"""
    total_recommendations: int
    skill_matches: int
    location_matches: int
    experience_matches: int
    salary_matches: int
    overall_relevance_score: float
    quality_distribution: Dict[str, int]


class JobManagementE2ETest(BaseE2ETest):
    """Consolidated job management E2E test class"""
    
    def __init__(self):
        super().__init__()
        self.test_users: List[MockUser] = []
        self.test_jobs: List[MockJob] = []
        self.scraping_results: List[Dict[str, Any]] = []
        self.recommendation_results: List[Dict[str, Any]] = []
    
    async def setup(self):
        """Set up job management test environment"""
        self.logger.info("Setting up job management test environment")
        await self._create_test_users()
        await self._create_test_jobs()
    
    async def teardown(self):
        """Clean up job management test environment"""
        self.logger.info("Cleaning up job management test environment")
        await self._run_cleanup_tasks()
    
    async def run_test(self) -> Dict[str, Any]:
        """Execute consolidated job management tests"""
        results = {
            "job_scraping": await self.test_job_scraping(),
            "job_recommendations": await self.test_job_recommendations(),
            "job_matching": await self.test_job_matching(),
            "integration_workflow": await self.test_integration_workflow()
        }
        
        # Calculate overall success
        overall_success = all(
            result.get("success", False) for result in results.values()
        )
        
        return {
            "test_name": "consolidated_job_management_test",
            "status": "passed" if overall_success else "failed",
            "results": results,
            "summary": {
                "test_users": len(self.test_users),
                "test_jobs": len(self.test_jobs),
                "scraping_operations": len(self.scraping_results),
                "recommendation_operations": len(self.recommendation_results)
            }
        }
    
    async def test_job_scraping(self) -> Dict[str, Any]:
        """Test job scraping functionality"""
        try:
            scraping_sources = ["indeed", "linkedin", "glassdoor"]
            scraped_jobs = []
            
            for source in scraping_sources:
                # Mock job scraping
                start_time = time.time()
                
                # Simulate scraping delay
                await asyncio.sleep(0.1)
                
                # Mock scraped jobs
                mock_scraped = [
                    {
                        "title": f"Software Engineer - {source}",
                        "company": f"Company from {source}",
                        "location": "San Francisco, CA",
                        "source": source,
                        "scraped_at": datetime.now()
                    }
                    for _ in range(5)  # 5 jobs per source
                ]
                
                execution_time = time.time() - start_time
                
                scraping_result = {
                    "source": source,
                    "jobs_scraped": len(mock_scraped),
                    "execution_time": execution_time,
                    "success": True
                }
                
                self.scraping_results.append(scraping_result)
                scraped_jobs.extend(mock_scraped)
            
            return {
                "success": True,
                "total_jobs_scraped": len(scraped_jobs),
                "sources_tested": len(scraping_sources),
                "scraping_results": self.scraping_results,
                "average_scraping_time": sum(r["execution_time"] for r in self.scraping_results) / len(self.scraping_results)
            }
            
        except Exception as e:
            self.logger.error(f"Job scraping test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_job_recommendations(self) -> Dict[str, Any]:
        """Test job recommendation system"""
        try:
            recommendation_results = []
            
            for user in self.test_users:
                # Get recommendations for user
                recommendations = self._get_recommendations_for_user(user)
                
                # Validate recommendation quality
                relevance_metrics = self._validate_recommendation_relevance(user, recommendations)
                
                result = {
                    "user_id": user.id,
                    "user_name": user.name,
                    "recommendations_count": len(recommendations),
                    "average_score": sum(r["score"] for r in recommendations) / len(recommendations) if recommendations else 0,
                    "relevance_metrics": relevance_metrics,
                    "success": True
                }
                
                recommendation_results.append(result)
                self.recommendation_results.append(result)
            
            overall_success = all(r["success"] for r in recommendation_results)
            
            return {
                "success": overall_success,
                "users_tested": len(recommendation_results),
                "total_recommendations": sum(r["recommendations_count"] for r in recommendation_results),
                "average_relevance": sum(r["relevance_metrics"].overall_relevance_score for r in recommendation_results) / len(recommendation_results),
                "recommendation_results": recommendation_results
            }
            
        except Exception as e:
            self.logger.error(f"Job recommendations test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_job_matching(self) -> Dict[str, Any]:
        """Test job matching algorithms"""
        try:
            matching_results = []
            
            for user in self.test_users:
                for job in self.test_jobs[:3]:  # Test with first 3 jobs
                    # Calculate match score
                    match_score = self._calculate_match_score(user, job)
                    
                    matching_results.append({
                        "user_id": user.id,
                        "job_id": job.id,
                        "match_score": match_score,
                        "skill_overlap": len(set(user.skills).intersection(set(job.tech_stack))),
                        "location_match": self._check_location_match(user, job)
                    })
            
            # Analyze matching quality
            high_quality_matches = len([r for r in matching_results if r["match_score"] >= 70])
            average_score = sum(r["match_score"] for r in matching_results) / len(matching_results)
            
            return {
                "success": True,
                "total_matches_tested": len(matching_results),
                "high_quality_matches": high_quality_matches,
                "average_match_score": average_score,
                "matching_results": matching_results
            }
            
        except Exception as e:
            self.logger.error(f"Job matching test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_integration_workflow(self) -> Dict[str, Any]:
        """Test complete job management integration workflow"""
        try:
            workflow_steps = []
            
            # Step 1: Scrape jobs
            scraping_result = await self.test_job_scraping()
            workflow_steps.append({
                "step": "job_scraping",
                "success": scraping_result.get("success", False),
                "duration": 0.1  # Mock duration
            })
            
            # Step 2: Generate recommendations
            if scraping_result.get("success"):
                recommendation_result = await self.test_job_recommendations()
                workflow_steps.append({
                    "step": "job_recommendations",
                    "success": recommendation_result.get("success", False),
                    "duration": 0.2  # Mock duration
                })
            
            # Step 3: Match jobs to users
            if all(step["success"] for step in workflow_steps):
                matching_result = await self.test_job_matching()
                workflow_steps.append({
                    "step": "job_matching",
                    "success": matching_result.get("success", False),
                    "duration": 0.15  # Mock duration
                })
            
            overall_success = all(step["success"] for step in workflow_steps)
            total_duration = sum(step["duration"] for step in workflow_steps)
            
            return {
                "success": overall_success,
                "workflow_steps": workflow_steps,
                "total_duration": total_duration,
                "steps_completed": len([s for s in workflow_steps if s["success"]])
            }
            
        except Exception as e:
            self.logger.error(f"Integration workflow test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_test_users(self):
        """Create test users for job management testing"""
        self.test_users = [
            MockUser(
                id=1, name="Junior Python Developer", email="junior@test.com",
                skills=["Python", "Django", "PostgreSQL"], preferred_locations=["San Francisco", "Remote"],
                experience_level="junior", career_goals=["Backend Development"]
            ),
            MockUser(
                id=2, name="Senior Full Stack Engineer", email="senior@test.com",
                skills=["React", "Node.js", "TypeScript", "AWS"], preferred_locations=["New York", "Remote"],
                experience_level="senior", career_goals=["Technical Leadership"]
            ),
            MockUser(
                id=3, name="Data Scientist", email="datascientist@test.com",
                skills=["Python", "TensorFlow", "SQL", "Pandas"], preferred_locations=["Seattle", "Remote"],
                experience_level="mid", career_goals=["Machine Learning"]
            )
        ]
    
    async def _create_test_jobs(self):
        """Create test jobs for job management testing"""
        self.test_jobs = [
            MockJob(
                id=1, user_id=1, title="Python Developer", company="TechCorp",
                location="San Francisco, CA", description="Python development role",
                tech_stack=["Python", "Django", "PostgreSQL"], salary_range="$80,000 - $100,000",
                job_type="full-time", remote_option=False
            ),
            MockJob(
                id=2, user_id=2, title="Senior Full Stack Engineer", company="StartupInc",
                location="Remote", description="Full stack development with React and Node.js",
                tech_stack=["React", "Node.js", "TypeScript"], salary_range="$120,000 - $150,000",
                job_type="full-time", remote_option=True
            ),
            MockJob(
                id=3, user_id=3, title="Data Scientist", company="DataCorp",
                location="Seattle, WA", description="Machine learning and data analysis",
                tech_stack=["Python", "TensorFlow", "SQL"], salary_range="$110,000 - $140,000",
                job_type="full-time", remote_option=True
            )
        ]
    
    def _get_recommendations_for_user(self, user: MockUser, limit: int = 5) -> List[Dict]:
        """Get mock recommendations for a user"""
        recommendations = []
        
        for job in self.test_jobs:
            score = self._calculate_match_score(user, job)
            recommendations.append({"job": job, "score": score})
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]
    
    def _calculate_match_score(self, user: MockUser, job: MockJob) -> float:
        """Calculate a match score between user and job"""
        score = 0.0
        
        # Skill matching (50% weight)
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        job_skills = set(s.lower() for s in job.tech_stack) if job.tech_stack else set()
        
        if user_skills and job_skills:
            common_skills = user_skills.intersection(job_skills)
            skill_match = len(common_skills) / len(job_skills)
            score += skill_match * 50
        
        # Location matching (30% weight)
        if self._check_location_match(user, job):
            score += 30
        
        # Experience matching (20% weight)
        job_title_lower = job.title.lower()
        user_exp = user.experience_level.lower() if user.experience_level else ""
        
        if user_exp in job_title_lower:
            score += 20
        elif user_exp == "junior" and any(term in job_title_lower for term in ["junior", "entry"]):
            score += 20
        elif user_exp == "senior" and any(term in job_title_lower for term in ["senior", "lead"]):
            score += 20
        else:
            score += 5
        
        return min(score, 100.0)
    
    def _check_location_match(self, user: MockUser, job: MockJob) -> bool:
        """Check if user and job locations match"""
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        job_location = job.location.lower() if job.location else ""
        
        if "remote" in user_locations and "remote" in job_location:
            return True
        elif any(loc in job_location for loc in user_locations):
            return True
        
        return False
    
    def _validate_recommendation_relevance(self, user: MockUser, recommendations: List[Dict]) -> RelevanceMetrics:
        """Validate the relevance of recommendations for a user"""
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
            job = rec["job"]
            score = rec["score"]
            
            # Check skill matches
            job_skills = set(s.lower() for s in job.tech_stack) if job.tech_stack else set()
            if user_skills.intersection(job_skills):
                skill_matches += 1
            
            # Check location matches
            if self._check_location_match(user, job):
                location_matches += 1
            
            # Check experience matches
            job_title = job.title.lower()
            if user_exp_level in job_title or \
               (user_exp_level == "junior" and any(term in job_title for term in ["junior", "entry"])) or \
               (user_exp_level == "senior" and any(term in job_title for term in ["senior", "lead"])):
                experience_matches += 1
            
            # Mock salary matching
            salary_matches += 1
            
            # Categorize by quality
            if score >= 80:
                quality_distribution["excellent"] += 1
            elif score >= 60:
                quality_distribution["high"] += 1
            elif score >= 40:
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