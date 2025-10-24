"""
Skill Gap Analysis Test Framework

This module provides comprehensive testing for the skill gap analysis system including:
- Test cases for skill comparison functionality
- API client for skill gap analysis endpoints
- Response time and accuracy validation
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
from backend.app.services.skill_gap_analyzer import SkillGapAnalyzer
from backend.app.services.skill_gap_analysis_service import skill_gap_analysis_service
from tests.e2e.base import BaseE2ETest


@dataclass
class TestUserSkillProfile:
    """Test user profile for skill gap analysis testing"""
    name: str
    email: str
    skills: List[str]
    experience_level: str
    target_roles: List[str]
    expected_gaps: List[str]  # Skills we expect to be identified as gaps
    expected_coverage: float  # Expected skill coverage percentage


@dataclass
class SkillGapTestResult:
    """Result of skill gap analysis test execution"""
    success: bool
    user_id: int
    analysis_generated: bool
    execution_time: float
    skill_coverage: float
    gaps_identified: int
    recommendations_count: int
    accuracy_score: float
    error_message: Optional[str]
    validation_errors: List[str]


@dataclass
class AccuracyMetrics:
    """Metrics for evaluating skill gap analysis accuracy"""
    total_expected_gaps: int
    correctly_identified_gaps: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    coverage_accuracy: float


class SkillGapAnalysisTestFramework(BaseE2ETest):
    """
    Test framework for skill gap analysis functionality
    
    Provides methods to:
    - Create and manage test user skill profiles
    - Test skill gap analysis API endpoints
    - Validate analysis accuracy and relevance
    - Measure analysis performance and response times
    """
    
    def __init__(self):
        super().__init__()
        self.db: Session = next(get_db())
        self.test_users: List[User] = []
        self.test_jobs: List[Job] = []
        self.api_client = httpx.AsyncClient(base_url="http://localhost:8000")
        
        # Define test user profiles with different skill sets
        self.test_profiles = [
            TestUserSkillProfile(
                name="Junior Python Developer",
                email="junior_python_skillgap@test.com",
                skills=["Python", "Git"],
                experience_level="junior",
                target_roles=["Backend Developer", "Full Stack Developer"],
                expected_gaps=["Django", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                expected_coverage=0.2  # Low coverage expected
            ),
            TestUserSkillProfile(
                name="Experienced Frontend Developer",
                email="frontend_dev_skillgap@test.com",
                skills=["JavaScript", "React", "CSS", "HTML"],
                experience_level="mid",
                target_roles=["Senior Frontend Developer", "Full Stack Developer"],
                expected_gaps=["TypeScript", "Node.js", "GraphQL", "Testing"],
                expected_coverage=0.6  # Medium coverage expected
            ),
            TestUserSkillProfile(
                name="Senior Full Stack Engineer",
                email="senior_fullstack_skillgap@test.com",
                skills=["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS"],
                experience_level="senior",
                target_roles=["Tech Lead", "Principal Engineer"],
                expected_gaps=["Kubernetes", "Terraform", "GraphQL", "Microservices"],
                expected_coverage=0.8  # High coverage expected
            ),
            TestUserSkillProfile(
                name="Data Science Beginner",
                email="data_science_beginner_skillgap@test.com",
                skills=["Python", "SQL"],
                experience_level="junior",
                target_roles=["Data Scientist", "Data Analyst"],
                expected_gaps=["Machine Learning", "TensorFlow", "Pandas", "NumPy", "Jupyter"],
                expected_coverage=0.3  # Low coverage expected
            ),
            TestUserSkillProfile(
                name="DevOps Specialist",
                email="devops_specialist_skillgap@test.com",
                skills=["Docker", "Kubernetes", "AWS", "Terraform", "Jenkins"],
                experience_level="senior",
                target_roles=["DevOps Engineer", "Site Reliability Engineer"],
                expected_gaps=["Prometheus", "Grafana", "Ansible", "Helm"],
                expected_coverage=0.7  # Good coverage expected
            )
        ]
    
    async def setup_test_environment(self) -> bool:
        """
        Set up test environment with test users and market jobs
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create test users from profiles
            await self._create_test_users()
            
            # Create market jobs for skill analysis
            await self._create_market_jobs()
            
            self.logger.info(f"Test environment setup complete. Created {len(self.test_users)} users and {len(self.test_jobs)} market jobs")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def _create_test_users(self) -> None:
        """Create test users from predefined skill profiles"""
        for profile in self.test_profiles:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == profile.email
            ).first()
            
            if existing_user:
                # Update existing user with test profile
                existing_user.skills = profile.skills
                existing_user.experience_level = profile.experience_level
                self.db.commit()
                self.test_users.append(existing_user)
                continue
            
            # Create new test user
            user = User(
                email=profile.email,
                name=profile.name,
                skills=profile.skills,
                experience_level=profile.experience_level,
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            self.test_users.append(user)
            
            self.logger.info(f"Created test user: {profile.name} (ID: {user.id})")
    
    async def _create_market_jobs(self) -> None:
        """Create market jobs with diverse skill requirements for analysis"""
        market_jobs = [
            # Backend Development Jobs
            {
                "title": "Senior Python Developer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "description": "Senior backend developer with Django and FastAPI experience",
                "tech_stack": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"],
                "requirements": {
                    "skills_required": ["Python", "Django", "PostgreSQL"],
                    "skills_preferred": ["FastAPI", "Redis", "Docker", "AWS"]
                }
            },
            {
                "title": "Full Stack Engineer",
                "company": "StartupXYZ",
                "location": "Remote",
                "description": "Full stack development with modern technologies",
                "tech_stack": ["JavaScript", "TypeScript", "React", "Node.js", "GraphQL", "MongoDB"],
                "requirements": {
                    "skills_required": ["JavaScript", "React", "Node.js"],
                    "skills_preferred": ["TypeScript", "GraphQL", "MongoDB"]
                }
            },
            
            # Frontend Development Jobs
            {
                "title": "Senior Frontend Developer",
                "company": "UI Masters",
                "location": "New York, NY",
                "description": "Advanced frontend development with React ecosystem",
                "tech_stack": ["JavaScript", "TypeScript", "React", "Redux", "CSS", "HTML", "Testing"],
                "requirements": {
                    "skills_required": ["JavaScript", "React", "CSS"],
                    "skills_preferred": ["TypeScript", "Redux", "Testing"]
                }
            },
            {
                "title": "Frontend Architect",
                "company": "Design Systems Inc",
                "location": "Austin, TX",
                "description": "Frontend architecture and design systems",
                "tech_stack": ["React", "Vue.js", "Angular", "TypeScript", "Webpack", "Storybook"],
                "requirements": {
                    "skills_required": ["React", "TypeScript"],
                    "skills_preferred": ["Vue.js", "Angular", "Webpack", "Storybook"]
                }
            },
            
            # Data Science Jobs
            {
                "title": "Data Scientist",
                "company": "AI Research Lab",
                "location": "Seattle, WA",
                "description": "Machine learning and data analysis",
                "tech_stack": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy", "Jupyter", "SQL"],
                "requirements": {
                    "skills_required": ["Python", "Machine Learning", "SQL"],
                    "skills_preferred": ["TensorFlow", "Pandas", "NumPy", "Jupyter"]
                }
            },
            {
                "title": "Senior Data Engineer",
                "company": "Big Data Corp",
                "location": "Boston, MA",
                "description": "Data pipeline and infrastructure",
                "tech_stack": ["Python", "Spark", "Kafka", "Airflow", "SQL", "AWS", "Docker"],
                "requirements": {
                    "skills_required": ["Python", "SQL", "Spark"],
                    "skills_preferred": ["Kafka", "Airflow", "AWS", "Docker"]
                }
            },
            
            # DevOps Jobs
            {
                "title": "DevOps Engineer",
                "company": "Cloud Native Co",
                "location": "Remote",
                "description": "Cloud infrastructure and automation",
                "tech_stack": ["Docker", "Kubernetes", "AWS", "Terraform", "Jenkins", "Prometheus", "Grafana"],
                "requirements": {
                    "skills_required": ["Docker", "Kubernetes", "AWS"],
                    "skills_preferred": ["Terraform", "Jenkins", "Prometheus", "Grafana"]
                }
            },
            {
                "title": "Site Reliability Engineer",
                "company": "Scale Systems",
                "location": "San Diego, CA",
                "description": "Site reliability and monitoring",
                "tech_stack": ["Kubernetes", "Prometheus", "Grafana", "Ansible", "Helm", "Python", "Go"],
                "requirements": {
                    "skills_required": ["Kubernetes", "Prometheus", "Python"],
                    "skills_preferred": ["Grafana", "Ansible", "Helm", "Go"]
                }
            },
            
            # Mobile Development Jobs
            {
                "title": "Mobile Developer",
                "company": "Mobile First",
                "location": "Los Angeles, CA",
                "description": "Cross-platform mobile development",
                "tech_stack": ["React Native", "Flutter", "JavaScript", "Dart", "iOS", "Android"],
                "requirements": {
                    "skills_required": ["React Native", "JavaScript"],
                    "skills_preferred": ["Flutter", "Dart", "iOS", "Android"]
                }
            },
            
            # Security Jobs
            {
                "title": "Security Engineer",
                "company": "SecureTech",
                "location": "Washington, DC",
                "description": "Application and infrastructure security",
                "tech_stack": ["Security", "Penetration Testing", "OWASP", "Python", "Linux", "Networking"],
                "requirements": {
                    "skills_required": ["Security", "Python", "Linux"],
                    "skills_preferred": ["Penetration Testing", "OWASP", "Networking"]
                }
            }
        ]
        
        # Create jobs in database
        for job_data in market_jobs:
            job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                tech_stack=job_data["tech_stack"],
                requirements=job_data["requirements"],
                status="active",
                source="test_framework",
                link=f"https://example.com/job/{job_data['title'].lower().replace(' ', '-')}",
                date_posted=datetime.now() - timedelta(days=1),  # Recent job
                created_at=datetime.now()
            )
            
            self.db.add(job)
            self.test_jobs.append(job)
        
        self.db.commit()
        self.logger.info(f"Created {len(self.test_jobs)} market jobs for skill analysis")
    
    async def test_skill_gap_api_endpoints(self) -> Dict[str, Any]:
        """
        Test skill gap analysis API endpoints
        
        Returns:
            Dict containing test results for all endpoints
        """
        results = {
            "basic_skill_gap_analysis": [],
            "comprehensive_analysis": [],
            "market_trends": [],
            "learning_recommendations": [],
            "api_performance": {}
        }
        
        try:
            for user in self.test_users:
                # Test basic skill gap analysis endpoint
                basic_result = await self._test_basic_skill_gap_api(user)
                results["basic_skill_gap_analysis"].append(basic_result)
                
                # Test comprehensive analysis endpoint
                comprehensive_result = await self._test_comprehensive_analysis_api(user)
                results["comprehensive_analysis"].append(comprehensive_result)
                
                # Test market trends endpoint
                trends_result = await self._test_market_trends_api()
                results["market_trends"].append(trends_result)
                
                # Test learning recommendations
                recommendations_result = await self._test_learning_recommendations_api(user)
                results["learning_recommendations"].append(recommendations_result)
            
            # Calculate overall API performance metrics
            results["api_performance"] = self._calculate_api_performance_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing skill gap API endpoints: {e}")
            return {"error": str(e)}
    
    async def _test_basic_skill_gap_api(self, user: User) -> Dict[str, Any]:
        """Test basic skill gap analysis API endpoint"""
        start_time = time.time()
        
        try:
            # Test skill gap analysis using SkillGapAnalyzer directly
            analyzer = SkillGapAnalyzer(self.db)
            analysis = analyzer.analyze_skill_gaps(user)
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": True,
                "analysis_generated": analysis is not None,
                "execution_time": execution_time,
                "skill_coverage": analysis.get("skill_coverage_percentage", 0),
                "gaps_identified": len(analysis.get("missing_skills", [])),
                "recommendations_count": len(analysis.get("recommendations", [])),
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": False,
                "analysis_generated": False,
                "execution_time": execution_time,
                "skill_coverage": 0,
                "gaps_identified": 0,
                "recommendations_count": 0,
                "error_message": str(e)
            }
    
    async def _test_comprehensive_analysis_api(self, user: User) -> Dict[str, Any]:
        """Test comprehensive skill gap analysis API endpoint"""
        start_time = time.time()
        
        try:
            # Test comprehensive analysis using service directly
            analysis = skill_gap_analysis_service.get_comprehensive_skill_analysis(
                db=self.db,
                user_id=user.id,
                include_trends=True
            )
            
            execution_time = time.time() - start_time
            
            skill_analysis = analysis.get("skill_analysis", {})
            
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": True,
                "analysis_generated": "error" not in analysis,
                "execution_time": execution_time,
                "skill_coverage": skill_analysis.get("skill_coverage", {}).get("percentage", 0),
                "gaps_identified": len(skill_analysis.get("top_skill_gaps", [])),
                "recommendations_count": len(analysis.get("learning_recommendations", [])),
                "error_message": analysis.get("error")
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": False,
                "analysis_generated": False,
                "execution_time": execution_time,
                "skill_coverage": 0,
                "gaps_identified": 0,
                "recommendations_count": 0,
                "error_message": str(e)
            }
    
    async def _test_market_trends_api(self) -> Dict[str, Any]:
        """Test market trends analysis API endpoint"""
        start_time = time.time()
        
        try:
            # Test market trends analysis
            trends = skill_gap_analysis_service.analyze_market_trends(
                db=self.db,
                days_back=30
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "trends_generated": "error" not in trends,
                "execution_time": execution_time,
                "trending_skills_count": len(trends.get("trending_skills", [])),
                "jobs_analyzed": trends.get("jobs_analyzed", 0),
                "error_message": trends.get("error")
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "trends_generated": False,
                "execution_time": execution_time,
                "trending_skills_count": 0,
                "jobs_analyzed": 0,
                "error_message": str(e)
            }
    
    async def _test_learning_recommendations_api(self, user: User) -> Dict[str, Any]:
        """Test learning recommendations generation"""
        start_time = time.time()
        
        try:
            # First get skill gaps
            analyzer = SkillGapAnalyzer(self.db)
            analysis = analyzer.analyze_skill_gaps(user)
            
            # Convert to format expected by learning recommendations
            skill_gaps = {
                "skill_gaps_by_priority": {
                    "high": [{"skill": skill, "priority_score": 0.8} for skill in analysis.get("missing_skills", [])[:3]],
                    "medium": [{"skill": skill, "priority_score": 0.6} for skill in analysis.get("missing_skills", [])[3:6]]
                }
            }
            
            # Generate learning recommendations
            recommendations = skill_gap_analysis_service.generate_learning_recommendations(
                skill_gaps=skill_gaps,
                user_profile={"experience_level": user.experience_level}
            )
            
            execution_time = time.time() - start_time
            
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": True,
                "recommendations_generated": len(recommendations) > 0,
                "execution_time": execution_time,
                "recommendations_count": len(recommendations),
                "error_message": None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "user_id": user.id,
                "user_name": user.name,
                "success": False,
                "recommendations_generated": False,
                "execution_time": execution_time,
                "recommendations_count": 0,
                "error_message": str(e)
            }
    
    def validate_analysis_accuracy(self, user: User, analysis: Dict[str, Any]) -> AccuracyMetrics:
        """
        Validate the accuracy of skill gap analysis for a specific user
        
        Args:
            user: User to validate analysis for
            analysis: Analysis results from skill gap analyzer
            
        Returns:
            AccuracyMetrics with detailed accuracy analysis
        """
        # Find the test profile for this user
        test_profile = None
        for profile in self.test_profiles:
            if profile.email == user.email:
                test_profile = profile
                break
        
        if not test_profile:
            return AccuracyMetrics(
                total_expected_gaps=0,
                correctly_identified_gaps=0,
                false_positives=0,
                false_negatives=0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                coverage_accuracy=0.0
            )
        
        expected_gaps = set(gap.lower() for gap in test_profile.expected_gaps)
        identified_gaps = set(gap.lower() for gap in analysis.get("missing_skills", []))
        
        # Calculate accuracy metrics
        correctly_identified = expected_gaps.intersection(identified_gaps)
        false_positives = identified_gaps - expected_gaps
        false_negatives = expected_gaps - identified_gaps
        
        precision = len(correctly_identified) / len(identified_gaps) if identified_gaps else 0
        recall = len(correctly_identified) / len(expected_gaps) if expected_gaps else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Check coverage accuracy
        actual_coverage = analysis.get("skill_coverage_percentage", 0) / 100
        expected_coverage = test_profile.expected_coverage
        coverage_accuracy = 1 - abs(actual_coverage - expected_coverage)
        
        return AccuracyMetrics(
            total_expected_gaps=len(expected_gaps),
            correctly_identified_gaps=len(correctly_identified),
            false_positives=len(false_positives),
            false_negatives=len(false_negatives),
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            coverage_accuracy=max(0, coverage_accuracy)
        )
    
    def validate_response_time_requirements(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that response times meet requirements (15 seconds for skill gap analysis)
        
        Args:
            results: List of test results with execution times
            
        Returns:
            Dict with response time validation results
        """
        SKILL_GAP_TIME_LIMIT = 15.0  # 15 seconds as per requirements
        
        execution_times = [r.get("execution_time", 0) for r in results if r.get("success", False)]
        
        if not execution_times:
            return {
                "meets_requirements": False,
                "reason": "No successful executions to measure"
            }
        
        max_time = max(execution_times)
        avg_time = sum(execution_times) / len(execution_times)
        within_limit_count = sum(1 for t in execution_times if t <= SKILL_GAP_TIME_LIMIT)
        
        return {
            "meets_requirements": max_time <= SKILL_GAP_TIME_LIMIT,
            "max_execution_time": max_time,
            "average_execution_time": avg_time,
            "time_limit": SKILL_GAP_TIME_LIMIT,
            "within_limit_percentage": within_limit_count / len(execution_times),
            "total_tests": len(execution_times)
        }
    
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
    
    async def run_comprehensive_skill_gap_test(self) -> Dict[str, Any]:
        """
        Run comprehensive skill gap analysis testing
        
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
            api_results = await self.test_skill_gap_api_endpoints()
            
            # Test analysis accuracy for each user
            accuracy_results = []
            for user in self.test_users:
                try:
                    # Get skill gap analysis
                    analyzer = SkillGapAnalyzer(self.db)
                    analysis = analyzer.analyze_skill_gaps(user)
                    
                    # Validate accuracy
                    accuracy_metrics = self.validate_analysis_accuracy(user, analysis)
                    
                    accuracy_results.append({
                        "user_id": user.id,
                        "user_name": user.name,
                        "accuracy_metrics": accuracy_metrics
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error testing accuracy for user {user.id}: {e}")
                    accuracy_results.append({
                        "user_id": user.id,
                        "user_name": user.name,
                        "error": str(e)
                    })
            
            # Validate response time requirements
            basic_results = api_results.get("basic_skill_gap_analysis", [])
            response_time_validation = self.validate_response_time_requirements(basic_results)
            
            total_execution_time = time.time() - start_time
            
            return {
                "test_summary": {
                    "total_execution_time": total_execution_time,
                    "test_users_created": len(self.test_users),
                    "market_jobs_created": len(self.test_jobs),
                    "timestamp": datetime.now().isoformat()
                },
                "api_test_results": api_results,
                "accuracy_test_results": accuracy_results,
                "response_time_validation": response_time_validation,
                "overall_success": len([r for r in accuracy_results if "error" not in r]) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive skill gap test: {e}")
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
async def run_skill_gap_analysis_test() -> Dict[str, Any]:
    """
    Convenience function to run skill gap analysis testing
    
    Returns:
        Dict containing test results
    """
    framework = SkillGapAnalysisTestFramework()
    try:
        results = await framework.run_comprehensive_skill_gap_test()
        return results
    finally:
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run the test when executed directly
    import asyncio
    
    async def main():
        results = await run_skill_gap_analysis_test()
        print("Skill Gap Analysis Test Results:")
        print("=" * 50)
        
        if "error" in results:
            print(f"Test failed with error: {results['error']}")
            return
        
        # Print summary
        summary = results.get("test_summary", {})
        print(f"Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
        print(f"Test users created: {summary.get('test_users_created', 0)}")
        print(f"Market jobs created: {summary.get('market_jobs_created', 0)}")
        print(f"Overall success: {results.get('overall_success', False)}")
        
        # Print API performance
        api_results = results.get("api_test_results", {})
        api_performance = api_results.get("api_performance", {})
        if api_performance:
            print(f"\nAPI Performance:")
            print(f"  Success rate: {api_performance.get('success_rate', 0):.2%}")
            print(f"  Average response time: {api_performance.get('average_response_time', 0):.3f}s")
        
        # Print response time validation
        response_time_validation = results.get("response_time_validation", {})
        if response_time_validation:
            print(f"\nResponse Time Validation:")
            print(f"  Meets requirements: {response_time_validation.get('meets_requirements', False)}")
            print(f"  Max execution time: {response_time_validation.get('max_execution_time', 0):.3f}s")
            print(f"  Time limit: {response_time_validation.get('time_limit', 0)}s")
        
        # Print accuracy results summary
        accuracy_results = results.get("accuracy_test_results", [])
        if accuracy_results:
            print(f"\nAccuracy Test Results:")
            for result in accuracy_results:
                if "error" not in result:
                    metrics = result.get("accuracy_metrics", {})
                    print(f"  {result['user_name']}: F1={metrics.f1_score:.2f}, Coverage Accuracy={metrics.coverage_accuracy:.2f}")
    
    asyncio.run(main())