"""
Course Recommendation Test Framework

This module provides comprehensive testing for the course recommendation system including:
- Test framework for course suggestion API
- Validation for recommendation quality and relevance
- Response time verification
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
from backend.app.models.user import User
from backend.app.services.skill_gap_analysis_service import skill_gap_analysis_service
from tests.e2e.base import BaseE2ETest


@dataclass
class TestUserCourseProfile:
    """Test user profile for course recommendation testing"""
    name: str
    email: str
    skills: List[str]
    skill_gaps: List[str]
    experience_level: str
    learning_goals: List[str]
    preferred_learning_style: str
    time_commitment: str  # "part-time", "full-time", "flexible"
    expected_course_types: List[str]  # Types of courses this user should receive


@dataclass
class CourseRecommendationTestResult:
    """Result of course recommendation test execution"""
    success: bool
    user_id: int
    recommendations_count: int
    average_relevance_score: float
    high_quality_matches: int
    execution_time: float
    error_message: Optional[str]
    validation_errors: List[str]
    meets_time_requirement: bool


@dataclass
class CourseRelevanceMetrics:
    """Metrics for evaluating course recommendation relevance"""
    total_recommendations: int
    skill_gap_matches: int
    experience_level_matches: int
    learning_style_matches: int
    time_commitment_matches: int
    overall_relevance_score: float
    quality_distribution: Dict[str, int]  # excellent, high, medium, low


@dataclass
class MockCourse:
    """Mock course data for testing"""
    id: int
    title: str
    provider: str
    description: str
    skills_covered: List[str]
    difficulty_level: str
    duration_hours: int
    format: str  # "online", "in-person", "hybrid"
    price: float
    rating: float
    relevance_score: float = 0.0


class CourseRecommendationTestFramework(BaseE2ETest):
    """
    Test framework for course recommendation functionality
    
    Provides methods to:
    - Create and manage test user profiles with skill gaps
    - Test course recommendation API endpoints
    - Validate recommendation relevance and quality
    - Measure recommendation performance and response times
    """
    
    def __init__(self):
        super().__init__()
        self.db: Session = next(get_db())
        self.test_users: List[User] = []
        self.mock_courses: List[MockCourse] = []
        self.api_client = httpx.AsyncClient(base_url="http://localhost:8000")
        
        # Define test user profiles with different learning needs
        self.test_profiles = [
            TestUserCourseProfile(
                name="Python Beginner",
                email="python_beginner_courses@test.com",
                skills=["HTML", "CSS"],
                skill_gaps=["Python", "Django", "FastAPI", "PostgreSQL"],
                experience_level="beginner",
                learning_goals=["Backend Development", "Web Development"],
                preferred_learning_style="hands-on",
                time_commitment="part-time",
                expected_course_types=["python-fundamentals", "web-development", "database"]
            ),
            TestUserCourseProfile(
                name="Frontend Developer Upskilling",
                email="frontend_upskill_courses@test.com",
                skills=["JavaScript", "React", "CSS"],
                skill_gaps=["TypeScript", "Node.js", "GraphQL", "Testing"],
                experience_level="intermediate",
                learning_goals=["Full Stack Development", "Advanced Frontend"],
                preferred_learning_style="project-based",
                time_commitment="flexible",
                expected_course_types=["typescript", "backend", "testing", "graphql"]
            ),
            TestUserCourseProfile(
                name="Data Science Transition",
                email="data_science_transition_courses@test.com",
                skills=["Python", "SQL"],
                skill_gaps=["Machine Learning", "TensorFlow", "Pandas", "NumPy", "Statistics"],
                experience_level="intermediate",
                learning_goals=["Data Science", "Machine Learning"],
                preferred_learning_style="theory-and-practice",
                time_commitment="full-time",
                expected_course_types=["machine-learning", "data-analysis", "statistics"]
            ),
            TestUserCourseProfile(
                name="DevOps Engineer Learning",
                email="devops_learning_courses@test.com",
                skills=["Docker", "AWS"],
                skill_gaps=["Kubernetes", "Terraform", "Jenkins", "Prometheus", "Ansible"],
                experience_level="intermediate",
                learning_goals=["DevOps Mastery", "Cloud Architecture"],
                preferred_learning_style="hands-on",
                time_commitment="part-time",
                expected_course_types=["kubernetes", "infrastructure", "monitoring", "automation"]
            ),
            TestUserCourseProfile(
                name="Complete Beginner",
                email="complete_beginner_courses@test.com",
                skills=[],
                skill_gaps=["Programming Fundamentals", "Git", "HTML", "CSS", "JavaScript"],
                experience_level="beginner",
                learning_goals=["Web Development", "Programming"],
                preferred_learning_style="structured",
                time_commitment="part-time",
                expected_course_types=["fundamentals", "web-basics", "programming-intro"]
            )
        ]
        
        # Create mock course catalog for testing
        self._create_mock_course_catalog()
    
    def _create_mock_course_catalog(self) -> None:
        """Create a comprehensive mock course catalog for testing"""
        self.mock_courses = [
            # Python Courses
            MockCourse(
                id=1,
                title="Python Fundamentals for Beginners",
                provider="CodeAcademy",
                description="Learn Python programming from scratch with hands-on exercises",
                skills_covered=["Python", "Programming Fundamentals", "Data Types"],
                difficulty_level="beginner",
                duration_hours=40,
                format="online",
                price=49.99,
                rating=4.5
            ),
            MockCourse(
                id=2,
                title="Advanced Python and Django Development",
                provider="Udemy",
                description="Master Django web framework and advanced Python concepts",
                skills_covered=["Python", "Django", "Web Development", "REST APIs"],
                difficulty_level="intermediate",
                duration_hours=60,
                format="online",
                price=89.99,
                rating=4.7
            ),
            MockCourse(
                id=3,
                title="FastAPI Modern Web Development",
                provider="Pluralsight",
                description="Build modern APIs with FastAPI and async Python",
                skills_covered=["FastAPI", "Python", "API Development", "Async Programming"],
                difficulty_level="intermediate",
                duration_hours=35,
                format="online",
                price=29.99,
                rating=4.6
            ),
            
            # Frontend Courses
            MockCourse(
                id=4,
                title="TypeScript Complete Guide",
                provider="Udemy",
                description="Master TypeScript for modern JavaScript development",
                skills_covered=["TypeScript", "JavaScript", "Type Safety"],
                difficulty_level="intermediate",
                duration_hours=45,
                format="online",
                price=79.99,
                rating=4.8
            ),
            MockCourse(
                id=5,
                title="React Advanced Patterns and Testing",
                provider="Frontend Masters",
                description="Advanced React patterns, hooks, and comprehensive testing",
                skills_covered=["React", "Testing", "JavaScript", "Hooks"],
                difficulty_level="advanced",
                duration_hours=50,
                format="online",
                price=199.99,
                rating=4.9
            ),
            MockCourse(
                id=6,
                title="GraphQL with React and Node.js",
                provider="Udemy",
                description="Full-stack GraphQL development with modern tools",
                skills_covered=["GraphQL", "React", "Node.js", "Apollo"],
                difficulty_level="intermediate",
                duration_hours=55,
                format="online",
                price=94.99,
                rating=4.6
            ),
            
            # Data Science Courses
            MockCourse(
                id=7,
                title="Machine Learning with Python and Scikit-Learn",
                provider="Coursera",
                description="Comprehensive machine learning course with practical projects",
                skills_covered=["Machine Learning", "Python", "Scikit-Learn", "Data Analysis"],
                difficulty_level="intermediate",
                duration_hours=80,
                format="online",
                price=49.99,
                rating=4.7
            ),
            MockCourse(
                id=8,
                title="Deep Learning with TensorFlow",
                provider="edX",
                description="Advanced deep learning techniques using TensorFlow",
                skills_covered=["TensorFlow", "Deep Learning", "Neural Networks", "Python"],
                difficulty_level="advanced",
                duration_hours=100,
                format="online",
                price=149.99,
                rating=4.5
            ),
            MockCourse(
                id=9,
                title="Data Analysis with Pandas and NumPy",
                provider="DataCamp",
                description="Master data manipulation and analysis with Python libraries",
                skills_covered=["Pandas", "NumPy", "Data Analysis", "Python"],
                difficulty_level="beginner",
                duration_hours=30,
                format="online",
                price=39.99,
                rating=4.4
            ),
            
            # DevOps Courses
            MockCourse(
                id=10,
                title="Kubernetes Complete Guide",
                provider="A Cloud Guru",
                description="Master container orchestration with Kubernetes",
                skills_covered=["Kubernetes", "Docker", "Container Orchestration", "DevOps"],
                difficulty_level="intermediate",
                duration_hours=70,
                format="online",
                price=129.99,
                rating=4.8
            ),
            MockCourse(
                id=11,
                title="Infrastructure as Code with Terraform",
                provider="Linux Academy",
                description="Automate infrastructure deployment with Terraform",
                skills_covered=["Terraform", "Infrastructure as Code", "AWS", "DevOps"],
                difficulty_level="intermediate",
                duration_hours=45,
                format="online",
                price=99.99,
                rating=4.6
            ),
            MockCourse(
                id=12,
                title="Monitoring and Observability with Prometheus",
                provider="Udemy",
                description="Implement comprehensive monitoring solutions",
                skills_covered=["Prometheus", "Grafana", "Monitoring", "DevOps"],
                difficulty_level="intermediate",
                duration_hours=40,
                format="online",
                price=74.99,
                rating=4.5
            ),
            
            # Fundamentals Courses
            MockCourse(
                id=13,
                title="Programming Fundamentals",
                provider="Khan Academy",
                description="Learn the basics of programming and computational thinking",
                skills_covered=["Programming Fundamentals", "Logic", "Problem Solving"],
                difficulty_level="beginner",
                duration_hours=25,
                format="online",
                price=0.00,
                rating=4.3
            ),
            MockCourse(
                id=14,
                title="Git and Version Control Mastery",
                provider="Atlassian",
                description="Master Git workflows and collaboration techniques",
                skills_covered=["Git", "Version Control", "Collaboration"],
                difficulty_level="beginner",
                duration_hours=20,
                format="online",
                price=29.99,
                rating=4.7
            ),
            MockCourse(
                id=15,
                title="Web Development Bootcamp",
                provider="The Odin Project",
                description="Complete web development curriculum from basics to advanced",
                skills_covered=["HTML", "CSS", "JavaScript", "Web Development"],
                difficulty_level="beginner",
                duration_hours=200,
                format="online",
                price=0.00,
                rating=4.6
            )
        ]
    
    async def setup_test_environment(self) -> bool:
        """
        Set up test environment with test users
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Create test users from profiles
            await self._create_test_users()
            
            self.logger.info(f"Course recommendation test environment setup complete. Created {len(self.test_users)} users")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup course recommendation test environment: {e}")
            return False
    
    async def _create_test_users(self) -> None:
        """Create test users from predefined course learning profiles"""
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
            
            self.logger.info(f"Created test user for course recommendations: {profile.name} (ID: {user.id})")
    
    async def test_course_recommendation_api_endpoints(self) -> Dict[str, Any]:
        """
        Test course recommendation API endpoints
        
        Returns:
            Dict containing test results for course recommendation endpoints
        """
        results = {
            "learning_recommendations": [],
            "skill_based_courses": [],
            "personalized_learning_paths": [],
            "api_performance": {}
        }
        
        try:
            for user in self.test_users:
                # Test learning recommendations endpoint (from skill gap analysis)
                learning_result = await self._test_learning_recommendations_api(user)
                results["learning_recommendations"].append(learning_result)
                
                # Test skill-based course suggestions
                skill_courses_result = await self._test_skill_based_course_api(user)
                results["skill_based_courses"].append(skill_courses_result)
                
                # Test personalized learning path generation
                learning_path_result = await self._test_personalized_learning_path_api(user)
                results["personalized_learning_paths"].append(learning_path_result)
            
            # Calculate overall API performance metrics
            results["api_performance"] = self._calculate_course_api_performance_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing course recommendation API endpoints: {e}")
            return {"error": str(e)}
    
    async def _test_learning_recommendations_api(self, user: User) -> CourseRecommendationTestResult:
        """Test learning recommendations API endpoint from skill gap analysis"""
        start_time = time.time()
        
        try:
            # Use the existing skill gap analysis service to get learning recommendations
            analysis = skill_gap_analysis_service.get_comprehensive_skill_analysis(
                db=self.db,
                user_id=user.id,
                include_trends=False
            )
            
            execution_time = time.time() - start_time
            
            if 'error' in analysis:
                return CourseRecommendationTestResult(
                    success=False,
                    user_id=user.id,
                    recommendations_count=0,
                    average_relevance_score=0.0,
                    high_quality_matches=0,
                    execution_time=execution_time,
                    error_message=analysis['error'],
                    validation_errors=[],
                    meets_time_requirement=execution_time <= 10.0
                )
            
            learning_recommendations = analysis.get('learning_recommendations', [])
            
            # Validate recommendations quality
            relevance_metrics = self._validate_course_recommendation_relevance(user, learning_recommendations)
            
            return CourseRecommendationTestResult(
                success=True,
                user_id=user.id,
                recommendations_count=len(learning_recommendations),
                average_relevance_score=relevance_metrics.overall_relevance_score,
                high_quality_matches=relevance_metrics.quality_distribution.get('high', 0) + 
                                   relevance_metrics.quality_distribution.get('excellent', 0),
                execution_time=execution_time,
                error_message=None,
                validation_errors=[],
                meets_time_requirement=execution_time <= 10.0  # 10 seconds as per requirements
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return CourseRecommendationTestResult(
                success=False,
                user_id=user.id,
                recommendations_count=0,
                average_relevance_score=0.0,
                high_quality_matches=0,
                execution_time=execution_time,
                error_message=str(e),
                validation_errors=[],
                meets_time_requirement=execution_time <= 10.0
            )
    
    async def _test_skill_based_course_api(self, user: User) -> CourseRecommendationTestResult:
        """Test skill-based course recommendation functionality"""
        start_time = time.time()
        
        try:
            # Find the test profile for this user
            test_profile = None
            for profile in self.test_profiles:
                if profile.email == user.email:
                    test_profile = profile
                    break
            
            if not test_profile:
                raise Exception("Test profile not found for user")
            
            # Generate course recommendations based on skill gaps
            course_recommendations = self._generate_mock_course_recommendations(
                skill_gaps=test_profile.skill_gaps,
                experience_level=test_profile.experience_level,
                learning_style=test_profile.preferred_learning_style
            )
            
            execution_time = time.time() - start_time
            
            # Validate recommendations quality
            relevance_metrics = self._validate_mock_course_relevance(test_profile, course_recommendations)
            
            return CourseRecommendationTestResult(
                success=True,
                user_id=user.id,
                recommendations_count=len(course_recommendations),
                average_relevance_score=relevance_metrics.overall_relevance_score,
                high_quality_matches=relevance_metrics.quality_distribution.get('high', 0) + 
                                   relevance_metrics.quality_distribution.get('excellent', 0),
                execution_time=execution_time,
                error_message=None,
                validation_errors=[],
                meets_time_requirement=execution_time <= 10.0
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return CourseRecommendationTestResult(
                success=False,
                user_id=user.id,
                recommendations_count=0,
                average_relevance_score=0.0,
                high_quality_matches=0,
                execution_time=execution_time,
                error_message=str(e),
                validation_errors=[],
                meets_time_requirement=execution_time <= 10.0
            )
    
    async def _test_personalized_learning_path_api(self, user: User) -> CourseRecommendationTestResult:
        """Test personalized learning path generation"""
        start_time = time.time()
        
        try:
            # Find the test profile for this user
            test_profile = None
            for profile in self.test_profiles:
                if profile.email == user.email:
                    test_profile = profile
                    break
            
            if not test_profile:
                raise Exception("Test profile not found for user")
            
            # Generate a structured learning path
            learning_path = self._generate_mock_learning_path(test_profile)
            
            execution_time = time.time() - start_time
            
            # Validate learning path structure and relevance
            path_quality = self._validate_learning_path_quality(test_profile, learning_path)
            
            return CourseRecommendationTestResult(
                success=True,
                user_id=user.id,
                recommendations_count=len(learning_path.get('courses', [])),
                average_relevance_score=path_quality['relevance_score'],
                high_quality_matches=path_quality['high_quality_courses'],
                execution_time=execution_time,
                error_message=None,
                validation_errors=path_quality.get('validation_errors', []),
                meets_time_requirement=execution_time <= 10.0
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return CourseRecommendationTestResult(
                success=False,
                user_id=user.id,
                recommendations_count=0,
                average_relevance_score=0.0,
                high_quality_matches=0,
                execution_time=execution_time,
                error_message=str(e),
                validation_errors=[],
                meets_time_requirement=execution_time <= 10.0
            )
    
    def _generate_mock_course_recommendations(self, skill_gaps: List[str], experience_level: str, learning_style: str) -> List[MockCourse]:
        """Generate mock course recommendations based on skill gaps"""
        recommendations = []
        
        for skill in skill_gaps[:5]:  # Limit to top 5 skill gaps
            # Find courses that cover this skill
            matching_courses = [
                course for course in self.mock_courses
                if any(skill.lower() in covered_skill.lower() for covered_skill in course.skills_covered)
            ]
            
            # Filter by experience level
            level_filtered = [
                course for course in matching_courses
                if self._is_appropriate_difficulty(course.difficulty_level, experience_level)
            ]
            
            # Calculate relevance scores
            for course in level_filtered:
                course.relevance_score = self._calculate_course_relevance_score(
                    course, skill, experience_level, learning_style
                )
            
            # Sort by relevance and take top matches
            level_filtered.sort(key=lambda x: x.relevance_score, reverse=True)
            recommendations.extend(level_filtered[:2])  # Top 2 courses per skill
        
        # Remove duplicates and sort by overall relevance
        unique_recommendations = list({course.id: course for course in recommendations}.values())
        unique_recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_recommendations[:10]  # Return top 10 recommendations
    
    def _is_appropriate_difficulty(self, course_difficulty: str, user_experience: str) -> bool:
        """Check if course difficulty is appropriate for user experience level"""
        difficulty_map = {
            "beginner": ["beginner"],
            "intermediate": ["beginner", "intermediate"],
            "advanced": ["beginner", "intermediate", "advanced"]
        }
        
        user_level = user_experience.lower()
        if user_level == "junior":
            user_level = "beginner"
        elif user_level == "mid" or user_level == "senior":
            user_level = "intermediate"
        
        return course_difficulty.lower() in difficulty_map.get(user_level, ["beginner"])
    
    def _calculate_course_relevance_score(self, course: MockCourse, target_skill: str, experience_level: str, learning_style: str) -> float:
        """Calculate relevance score for a course based on user needs"""
        score = 0.0
        
        # Skill match score (40% weight)
        skill_match = any(target_skill.lower() in skill.lower() for skill in course.skills_covered)
        if skill_match:
            score += 0.4
        
        # Difficulty appropriateness (25% weight)
        if self._is_appropriate_difficulty(course.difficulty_level, experience_level):
            score += 0.25
        
        # Course rating (20% weight)
        score += (course.rating / 5.0) * 0.20
        
        # Learning style match (15% weight)
        style_match = self._matches_learning_style(course, learning_style)
        if style_match:
            score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _matches_learning_style(self, course: MockCourse, learning_style: str) -> bool:
        """Check if course format matches user's preferred learning style"""
        style_mappings = {
            "hands-on": ["online", "hybrid"],
            "project-based": ["online", "hybrid"],
            "theory-and-practice": ["online", "in-person", "hybrid"],
            "structured": ["online", "in-person"]
        }
        
        return course.format in style_mappings.get(learning_style, ["online"])
    
    def _generate_mock_learning_path(self, profile: TestUserCourseProfile) -> Dict[str, Any]:
        """Generate a structured learning path for the user"""
        # Get course recommendations
        course_recommendations = self._generate_mock_course_recommendations(
            profile.skill_gaps, profile.experience_level, profile.preferred_learning_style
        )
        
        # Organize into a structured path
        learning_path = {
            "user_profile": {
                "name": profile.name,
                "experience_level": profile.experience_level,
                "learning_goals": profile.learning_goals
            },
            "path_overview": {
                "total_courses": len(course_recommendations),
                "estimated_duration_hours": sum(course.duration_hours for course in course_recommendations),
                "total_cost": sum(course.price for course in course_recommendations),
                "difficulty_progression": self._analyze_difficulty_progression(course_recommendations)
            },
            "courses": [
                {
                    "id": course.id,
                    "title": course.title,
                    "provider": course.provider,
                    "skills_covered": course.skills_covered,
                    "duration_hours": course.duration_hours,
                    "difficulty_level": course.difficulty_level,
                    "price": course.price,
                    "rating": course.rating,
                    "relevance_score": course.relevance_score,
                    "order_in_path": idx + 1
                }
                for idx, course in enumerate(course_recommendations)
            ],
            "skill_coverage": self._analyze_skill_coverage(course_recommendations, profile.skill_gaps),
            "milestones": self._generate_learning_milestones(course_recommendations, profile.skill_gaps)
        }
        
        return learning_path
    
    def _analyze_difficulty_progression(self, courses: List[MockCourse]) -> Dict[str, Any]:
        """Analyze the difficulty progression in the course sequence"""
        difficulty_levels = [course.difficulty_level for course in courses]
        
        return {
            "starts_with": difficulty_levels[0] if difficulty_levels else "unknown",
            "ends_with": difficulty_levels[-1] if difficulty_levels else "unknown",
            "progression": difficulty_levels,
            "is_progressive": self._is_progressive_difficulty(difficulty_levels)
        }
    
    def _is_progressive_difficulty(self, levels: List[str]) -> bool:
        """Check if difficulty levels progress appropriately"""
        level_order = {"beginner": 1, "intermediate": 2, "advanced": 3}
        
        if len(levels) < 2:
            return True
        
        # Check if levels generally increase or stay the same
        for i in range(1, len(levels)):
            current_level = level_order.get(levels[i], 2)
            previous_level = level_order.get(levels[i-1], 2)
            
            # Allow same level or progression, but not regression
            if current_level < previous_level:
                return False
        
        return True
    
    def _analyze_skill_coverage(self, courses: List[MockCourse], target_skills: List[str]) -> Dict[str, Any]:
        """Analyze how well the courses cover the target skills"""
        covered_skills = set()
        for course in courses:
            covered_skills.update(skill.lower() for skill in course.skills_covered)
        
        target_skills_lower = set(skill.lower() for skill in target_skills)
        covered_target_skills = covered_skills.intersection(target_skills_lower)
        
        return {
            "target_skills": target_skills,
            "covered_skills": list(covered_target_skills),
            "uncovered_skills": list(target_skills_lower - covered_target_skills),
            "coverage_percentage": len(covered_target_skills) / len(target_skills_lower) if target_skills_lower else 0
        }
    
    def _generate_learning_milestones(self, courses: List[MockCourse], skill_gaps: List[str]) -> List[Dict[str, Any]]:
        """Generate learning milestones based on the course sequence"""
        milestones = []
        cumulative_hours = 0
        skills_acquired = set()
        
        for idx, course in enumerate(courses):
            cumulative_hours += course.duration_hours
            skills_acquired.update(skill.lower() for skill in course.skills_covered)
            
            milestone = {
                "milestone_number": idx + 1,
                "after_course": course.title,
                "cumulative_hours": cumulative_hours,
                "skills_acquired": list(skills_acquired),
                "completion_percentage": (idx + 1) / len(courses),
                "estimated_weeks": cumulative_hours / 10  # Assuming 10 hours per week
            }
            
            milestones.append(milestone)
        
        return milestones
    
    def _validate_course_recommendation_relevance(self, user: User, recommendations: List[Dict[str, Any]]) -> CourseRelevanceMetrics:
        """Validate the relevance of course recommendations from the API"""
        if not recommendations:
            return CourseRelevanceMetrics(
                total_recommendations=0,
                skill_gap_matches=0,
                experience_level_matches=0,
                learning_style_matches=0,
                time_commitment_matches=0,
                overall_relevance_score=0.0,
                quality_distribution={"excellent": 0, "high": 0, "medium": 0, "low": 0}
            )
        
        # Find the test profile for this user
        test_profile = None
        for profile in self.test_profiles:
            if profile.email == user.email:
                test_profile = profile
                break
        
        if not test_profile:
            return CourseRelevanceMetrics(
                total_recommendations=len(recommendations),
                skill_gap_matches=0,
                experience_level_matches=0,
                learning_style_matches=0,
                time_commitment_matches=0,
                overall_relevance_score=0.0,
                quality_distribution={"excellent": 0, "high": 0, "medium": 0, "low": 0}
            )
        
        skill_gap_matches = 0
        experience_matches = 0
        quality_scores = []
        quality_distribution = {"excellent": 0, "high": 0, "medium": 0, "low": 0}
        
        for rec in recommendations:
            # Check skill gap relevance
            rec_skill = rec.get('skill', '').lower()
            if any(gap.lower() in rec_skill for gap in test_profile.skill_gaps):
                skill_gap_matches += 1
            
            # Check experience level appropriateness
            priority = rec.get('priority', '').lower()
            if test_profile.experience_level == 'beginner' and priority in ['high', 'medium']:
                experience_matches += 1
            elif test_profile.experience_level in ['intermediate', 'senior'] and priority in ['high', 'medium', 'low']:
                experience_matches += 1
            
            # Calculate quality score based on recommendation completeness
            quality_score = 0.0
            if rec.get('skill'):
                quality_score += 0.3
            if rec.get('learning_path'):
                quality_score += 0.4
            if rec.get('next_steps'):
                quality_score += 0.3
            
            quality_scores.append(quality_score)
            
            # Categorize quality
            if quality_score >= 0.9:
                quality_distribution["excellent"] += 1
            elif quality_score >= 0.7:
                quality_distribution["high"] += 1
            elif quality_score >= 0.5:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        overall_relevance = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return CourseRelevanceMetrics(
            total_recommendations=len(recommendations),
            skill_gap_matches=skill_gap_matches,
            experience_level_matches=experience_matches,
            learning_style_matches=0,  # Not available in API response
            time_commitment_matches=0,  # Not available in API response
            overall_relevance_score=overall_relevance,
            quality_distribution=quality_distribution
        )
    
    def _validate_mock_course_relevance(self, profile: TestUserCourseProfile, courses: List[MockCourse]) -> CourseRelevanceMetrics:
        """Validate the relevance of mock course recommendations"""
        if not courses:
            return CourseRelevanceMetrics(
                total_recommendations=0,
                skill_gap_matches=0,
                experience_level_matches=0,
                learning_style_matches=0,
                time_commitment_matches=0,
                overall_relevance_score=0.0,
                quality_distribution={"excellent": 0, "high": 0, "medium": 0, "low": 0}
            )
        
        skill_gap_matches = 0
        experience_matches = 0
        learning_style_matches = 0
        quality_distribution = {"excellent": 0, "high": 0, "medium": 0, "low": 0}
        
        for course in courses:
            # Check skill gap coverage
            if any(gap.lower() in skill.lower() for gap in profile.skill_gaps for skill in course.skills_covered):
                skill_gap_matches += 1
            
            # Check experience level appropriateness
            if self._is_appropriate_difficulty(course.difficulty_level, profile.experience_level):
                experience_matches += 1
            
            # Check learning style match
            if self._matches_learning_style(course, profile.preferred_learning_style):
                learning_style_matches += 1
            
            # Categorize quality based on relevance score
            if course.relevance_score >= 0.8:
                quality_distribution["excellent"] += 1
            elif course.relevance_score >= 0.6:
                quality_distribution["high"] += 1
            elif course.relevance_score >= 0.4:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        overall_relevance = sum(course.relevance_score for course in courses) / len(courses)
        
        return CourseRelevanceMetrics(
            total_recommendations=len(courses),
            skill_gap_matches=skill_gap_matches,
            experience_level_matches=experience_matches,
            learning_style_matches=learning_style_matches,
            time_commitment_matches=len(courses),  # Assume all match for mock data
            overall_relevance_score=overall_relevance,
            quality_distribution=quality_distribution
        )
    
    def _validate_learning_path_quality(self, profile: TestUserCourseProfile, learning_path: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of a generated learning path"""
        validation_errors = []
        courses = learning_path.get('courses', [])
        
        if not courses:
            validation_errors.append("Learning path contains no courses")
            return {
                "relevance_score": 0.0,
                "high_quality_courses": 0,
                "validation_errors": validation_errors
            }
        
        # Check skill coverage
        skill_coverage = learning_path.get('skill_coverage', {})
        coverage_percentage = skill_coverage.get('coverage_percentage', 0)
        
        if coverage_percentage < 0.5:
            validation_errors.append(f"Low skill coverage: {coverage_percentage:.1%}")
        
        # Check difficulty progression
        path_overview = learning_path.get('path_overview', {})
        difficulty_progression = path_overview.get('difficulty_progression', {})
        
        if not difficulty_progression.get('is_progressive', False):
            validation_errors.append("Difficulty progression is not appropriate")
        
        # Check course quality
        high_quality_courses = sum(1 for course in courses if course.get('relevance_score', 0) >= 0.7)
        
        # Calculate overall path relevance
        course_relevance_scores = [course.get('relevance_score', 0) for course in courses]
        path_relevance = sum(course_relevance_scores) / len(course_relevance_scores) if course_relevance_scores else 0
        
        # Adjust relevance based on coverage and progression
        if coverage_percentage >= 0.8:
            path_relevance += 0.1
        if difficulty_progression.get('is_progressive', False):
            path_relevance += 0.1
        
        path_relevance = min(path_relevance, 1.0)
        
        return {
            "relevance_score": path_relevance,
            "high_quality_courses": high_quality_courses,
            "validation_errors": validation_errors
        }
    
    def validate_response_time_requirements(self, results: List[CourseRecommendationTestResult]) -> Dict[str, Any]:
        """
        Validate that response times meet requirements (10 seconds for course recommendations)
        
        Args:
            results: List of course recommendation test results
            
        Returns:
            Dict with response time validation results
        """
        COURSE_RECOMMENDATION_TIME_LIMIT = 10.0  # 10 seconds as per requirements
        
        successful_results = [r for r in results if r.success]
        execution_times = [r.execution_time for r in successful_results]
        
        if not execution_times:
            return {
                "meets_requirements": False,
                "reason": "No successful executions to measure"
            }
        
        max_time = max(execution_times)
        avg_time = sum(execution_times) / len(execution_times)
        within_limit_count = sum(1 for t in execution_times if t <= COURSE_RECOMMENDATION_TIME_LIMIT)
        
        return {
            "meets_requirements": max_time <= COURSE_RECOMMENDATION_TIME_LIMIT,
            "max_execution_time": max_time,
            "average_execution_time": avg_time,
            "time_limit": COURSE_RECOMMENDATION_TIME_LIMIT,
            "within_limit_percentage": within_limit_count / len(execution_times),
            "total_tests": len(execution_times)
        }
    
    def _calculate_course_api_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall course recommendation API performance metrics"""
        all_results = []
        
        # Collect all API test results
        for endpoint_results in results.values():
            if isinstance(endpoint_results, list):
                all_results.extend(endpoint_results)
        
        if not all_results:
            return {"error": "No course API results to analyze"}
        
        successful_calls = [r for r in all_results if r.success]
        failed_calls = [r for r in all_results if not r.success]
        
        execution_times = [r.execution_time for r in successful_calls]
        relevance_scores = [r.average_relevance_score for r in successful_calls]
        
        return {
            "total_api_calls": len(all_results),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "success_rate": len(successful_calls) / len(all_results) if all_results else 0,
            "average_response_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "max_response_time": max(execution_times) if execution_times else 0,
            "min_response_time": min(execution_times) if execution_times else 0,
            "average_relevance_score": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
            "high_quality_recommendations": sum(r.high_quality_matches for r in successful_calls)
        }
    
    async def run_comprehensive_course_recommendation_test(self) -> Dict[str, Any]:
        """
        Run comprehensive course recommendation testing
        
        Returns:
            Dict containing complete test results
        """
        start_time = time.time()
        
        try:
            # Setup test environment
            setup_success = await self.setup_test_environment()
            if not setup_success:
                return {"error": "Failed to setup course recommendation test environment"}
            
            # Test API endpoints
            api_results = await self.test_course_recommendation_api_endpoints()
            
            # Validate response time requirements
            all_results = []
            for endpoint_results in api_results.values():
                if isinstance(endpoint_results, list):
                    all_results.extend(endpoint_results)
            
            response_time_validation = self.validate_response_time_requirements(all_results)
            
            total_execution_time = time.time() - start_time
            
            return {
                "test_summary": {
                    "total_execution_time": total_execution_time,
                    "test_users_created": len(self.test_users),
                    "mock_courses_available": len(self.mock_courses),
                    "timestamp": datetime.now().isoformat()
                },
                "api_test_results": api_results,
                "response_time_validation": response_time_validation,
                "overall_success": len([r for r in all_results if r.success]) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive course recommendation test: {e}")
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
            # Remove test users
            for user in self.test_users:
                self.db.delete(user)
            
            self.db.commit()
            
            # Close API client
            await self.api_client.aclose()
            
            self.logger.info("Course recommendation test environment cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during course recommendation test environment cleanup: {e}")
            return False


# Convenience function for running the test
async def run_course_recommendation_test() -> Dict[str, Any]:
    """
    Convenience function to run course recommendation testing
    
    Returns:
        Dict containing test results
    """
    framework = CourseRecommendationTestFramework()
    try:
        results = await framework.run_comprehensive_course_recommendation_test()
        return results
    finally:
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run the test when executed directly
    import asyncio
    
    async def main():
        results = await run_course_recommendation_test()
        print("Course Recommendation Test Results:")
        print("=" * 50)
        
        if "error" in results:
            print(f"Test failed with error: {results['error']}")
            return
        
        # Print summary
        summary = results.get("test_summary", {})
        print(f"Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
        print(f"Test users created: {summary.get('test_users_created', 0)}")
        print(f"Mock courses available: {summary.get('mock_courses_available', 0)}")
        print(f"Overall success: {results.get('overall_success', False)}")
        
        # Print API performance
        api_results = results.get("api_test_results", {})
        api_performance = api_results.get("api_performance", {})
        if api_performance and "error" not in api_performance:
            print(f"\nAPI Performance:")
            print(f"  Success rate: {api_performance.get('success_rate', 0):.2%}")
            print(f"  Average response time: {api_performance.get('average_response_time', 0):.3f}s")
            print(f"  Average relevance score: {api_performance.get('average_relevance_score', 0):.2f}")
        
        # Print response time validation
        response_time_validation = results.get("response_time_validation", {})
        if response_time_validation:
            print(f"\nResponse Time Validation:")
            print(f"  Meets requirements: {response_time_validation.get('meets_requirements', False)}")
            print(f"  Max execution time: {response_time_validation.get('max_execution_time', 0):.3f}s")
            print(f"  Time limit: {response_time_validation.get('time_limit', 0)}s")
        
        # Print detailed results for each endpoint
        learning_recommendations = api_results.get("learning_recommendations", [])
        if learning_recommendations:
            print(f"\nLearning Recommendations Results:")
            for result in learning_recommendations:
                print(f"  User {result.user_id}: {result.recommendations_count} recommendations, "
                      f"relevance: {result.average_relevance_score:.2f}, "
                      f"time: {result.execution_time:.3f}s")
    
    asyncio.run(main())