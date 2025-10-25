"""
Consolidated Course Recommendations E2E Tests

This module consolidates all course recommendation E2E tests including:
- Course recommendation generation
- Course matching algorithms
- Course recommendation validation
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from base import BaseE2ETest


@dataclass
class MockCourse:
    """Mock course for testing"""
    id: int
    title: str
    provider: str
    description: str
    skills_taught: List[str]
    difficulty_level: str
    duration_hours: int
    rating: float
    price: float
    category: str


@dataclass
class CourseRecommendation:
    """Course recommendation result"""
    course: MockCourse
    relevance_score: float
    skill_gap_addressed: List[str]
    learning_path_position: int
    estimated_completion_time: int


class CourseRecommendationsE2ETest(BaseE2ETest):
    """Consolidated course recommendations E2E test class"""
    
    def __init__(self):
        super().__init__()
        self.test_courses: List[MockCourse] = []
        self.recommendation_results: List[Dict[str, Any]] = []
    
    async def setup(self):
        """Set up course recommendations test environment"""
        self.logger.info("Setting up course recommendations test environment")
        await self._create_test_courses()
    
    async def teardown(self):
        """Clean up course recommendations test environment"""
        self.logger.info("Cleaning up course recommendations test environment")
        await self._run_cleanup_tasks()
    
    async def run_test(self) -> Dict[str, Any]:
        """Execute consolidated course recommendations tests"""
        results = {
            "recommendation_generation": await self.test_course_recommendation_generation(),
            "skill_gap_analysis": await self.test_skill_gap_analysis(),
            "learning_path_creation": await self.test_learning_path_creation(),
            "recommendation_validation": await self.test_recommendation_validation()
        }
        
        # Calculate overall success
        overall_success = all(
            result.get("success", False) for result in results.values()
        )
        
        return {
            "test_name": "consolidated_course_recommendations_test",
            "status": "passed" if overall_success else "failed",
            "results": results,
            "summary": {
                "total_courses": len(self.test_courses),
                "recommendation_operations": len(self.recommendation_results),
                "average_relevance_score": sum(
                    r.get("average_relevance", 0) for r in self.recommendation_results
                ) / len(self.recommendation_results) if self.recommendation_results else 0
            }
        }
    
    async def test_course_recommendation_generation(self) -> Dict[str, Any]:
        """Test course recommendation generation"""
        try:
            # Mock user profiles with different skill gaps
            test_users = [
                {
                    "id": 1,
                    "name": "Junior Developer",
                    "current_skills": ["Python", "HTML", "CSS"],
                    "target_skills": ["React", "Node.js", "Docker"],
                    "experience_level": "beginner"
                },
                {
                    "id": 2,
                    "name": "Mid-level Engineer",
                    "current_skills": ["JavaScript", "React", "SQL"],
                    "target_skills": ["TypeScript", "GraphQL", "AWS"],
                    "experience_level": "intermediate"
                },
                {
                    "id": 3,
                    "name": "Senior Developer",
                    "current_skills": ["Java", "Spring", "Microservices"],
                    "target_skills": ["Kubernetes", "Machine Learning", "System Design"],
                    "experience_level": "advanced"
                }
            ]
            
            recommendation_results = []
            
            for user in test_users:
                # Generate course recommendations for user
                recommendations = await self._generate_course_recommendations(user)
                
                result = {
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "recommendations_count": len(recommendations),
                    "average_relevance": sum(r.relevance_score for r in recommendations) / len(recommendations) if recommendations else 0,
                    "skill_gaps_addressed": len(set().union(*[r.skill_gap_addressed for r in recommendations])),
                    "success": len(recommendations) > 0
                }
                
                recommendation_results.append(result)
                self.recommendation_results.append(result)
            
            overall_success = all(r["success"] for r in recommendation_results)
            
            return {
                "success": overall_success,
                "users_tested": len(test_users),
                "total_recommendations": sum(r["recommendations_count"] for r in recommendation_results),
                "recommendation_results": recommendation_results
            }
            
        except Exception as e:
            self.logger.error(f"Course recommendation generation test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_skill_gap_analysis(self) -> Dict[str, Any]:
        """Test skill gap analysis functionality"""
        try:
            # Mock skill gap analysis scenarios
            skill_gap_scenarios = [
                {
                    "current_skills": ["Python", "SQL"],
                    "target_role": "Data Scientist",
                    "expected_gaps": ["Machine Learning", "Statistics", "Pandas", "NumPy"]
                },
                {
                    "current_skills": ["HTML", "CSS", "JavaScript"],
                    "target_role": "Full Stack Developer",
                    "expected_gaps": ["React", "Node.js", "Database Design", "API Development"]
                },
                {
                    "current_skills": ["Java", "Spring Boot"],
                    "target_role": "DevOps Engineer",
                    "expected_gaps": ["Docker", "Kubernetes", "AWS", "CI/CD"]
                }
            ]
            
            analysis_results = []
            
            for scenario in skill_gap_scenarios:
                # Perform skill gap analysis
                skill_gaps = await self._analyze_skill_gaps(
                    scenario["current_skills"],
                    scenario["target_role"]
                )
                
                # Validate analysis accuracy
                expected_gaps = set(scenario["expected_gaps"])
                identified_gaps = set(skill_gaps)
                
                # Calculate accuracy metrics
                correct_gaps = expected_gaps.intersection(identified_gaps)
                accuracy = len(correct_gaps) / len(expected_gaps) if expected_gaps else 0
                
                analysis_results.append({
                    "target_role": scenario["target_role"],
                    "expected_gaps": len(expected_gaps),
                    "identified_gaps": len(identified_gaps),
                    "correct_gaps": len(correct_gaps),
                    "accuracy": accuracy,
                    "success": accuracy >= 0.7  # 70% accuracy threshold
                })
            
            overall_success = all(r["success"] for r in analysis_results)
            average_accuracy = sum(r["accuracy"] for r in analysis_results) / len(analysis_results)
            
            return {
                "success": overall_success,
                "scenarios_tested": len(skill_gap_scenarios),
                "average_accuracy": average_accuracy,
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            self.logger.error(f"Skill gap analysis test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_learning_path_creation(self) -> Dict[str, Any]:
        """Test learning path creation"""
        try:
            # Mock learning path scenarios
            learning_scenarios = [
                {
                    "user_level": "beginner",
                    "target_skills": ["React", "Node.js", "MongoDB"],
                    "expected_path_length": 4,
                    "expected_duration": 120  # hours
                },
                {
                    "user_level": "intermediate",
                    "target_skills": ["Machine Learning", "TensorFlow"],
                    "expected_path_length": 3,
                    "expected_duration": 80  # hours
                },
                {
                    "user_level": "advanced",
                    "target_skills": ["System Design", "Microservices"],
                    "expected_path_length": 2,
                    "expected_duration": 60  # hours
                }
            ]
            
            path_results = []
            
            for scenario in learning_scenarios:
                # Create learning path
                learning_path = await self._create_learning_path(
                    scenario["user_level"],
                    scenario["target_skills"]
                )
                
                # Validate path structure
                path_valid = (
                    len(learning_path) >= scenario["expected_path_length"] - 1 and
                    len(learning_path) <= scenario["expected_path_length"] + 1
                )
                
                total_duration = sum(course.duration_hours for course in learning_path)
                duration_valid = (
                    total_duration >= scenario["expected_duration"] - 20 and
                    total_duration <= scenario["expected_duration"] + 40
                )
                
                path_results.append({
                    "user_level": scenario["user_level"],
                    "target_skills": scenario["target_skills"],
                    "path_length": len(learning_path),
                    "total_duration": total_duration,
                    "path_valid": path_valid,
                    "duration_valid": duration_valid,
                    "success": path_valid and duration_valid
                })
            
            overall_success = all(r["success"] for r in path_results)
            
            return {
                "success": overall_success,
                "scenarios_tested": len(learning_scenarios),
                "path_results": path_results
            }
            
        except Exception as e:
            self.logger.error(f"Learning path creation test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_recommendation_validation(self) -> Dict[str, Any]:
        """Test course recommendation validation"""
        try:
            # Mock validation scenarios
            validation_tests = []
            
            # Test 1: Relevance validation
            relevance_test = await self._test_recommendation_relevance()
            validation_tests.append(relevance_test)
            
            # Test 2: Difficulty progression validation
            progression_test = await self._test_difficulty_progression()
            validation_tests.append(progression_test)
            
            # Test 3: Skill coverage validation
            coverage_test = await self._test_skill_coverage()
            validation_tests.append(coverage_test)
            
            # Test 4: Duration estimation validation
            duration_test = await self._test_duration_estimation()
            validation_tests.append(duration_test)
            
            successful_tests = len([t for t in validation_tests if t["success"]])
            
            return {
                "success": successful_tests == len(validation_tests),
                "total_validation_tests": len(validation_tests),
                "successful_tests": successful_tests,
                "failed_tests": len(validation_tests) - successful_tests,
                "validation_results": validation_tests
            }
            
        except Exception as e:
            self.logger.error(f"Recommendation validation test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_test_courses(self):
        """Create test courses for recommendation testing"""
        self.test_courses = [
            # Frontend Development Courses
            MockCourse(
                id=1, title="React Fundamentals", provider="TechEd",
                description="Learn React basics and component development",
                skills_taught=["React", "JSX", "Component Architecture"],
                difficulty_level="beginner", duration_hours=30, rating=4.5, price=99.0,
                category="Frontend Development"
            ),
            MockCourse(
                id=2, title="Advanced React Patterns", provider="DevAcademy",
                description="Master advanced React patterns and hooks",
                skills_taught=["React", "Hooks", "Context API", "Performance Optimization"],
                difficulty_level="advanced", duration_hours=40, rating=4.7, price=149.0,
                category="Frontend Development"
            ),
            
            # Backend Development Courses
            MockCourse(
                id=3, title="Node.js Complete Guide", provider="CodeSchool",
                description="Full-stack development with Node.js and Express",
                skills_taught=["Node.js", "Express", "REST APIs", "Authentication"],
                difficulty_level="intermediate", duration_hours=50, rating=4.6, price=129.0,
                category="Backend Development"
            ),
            MockCourse(
                id=4, title="Database Design Fundamentals", provider="DataLearn",
                description="Learn database design and SQL optimization",
                skills_taught=["SQL", "Database Design", "Query Optimization", "Indexing"],
                difficulty_level="beginner", duration_hours=25, rating=4.4, price=79.0,
                category="Database"
            ),
            
            # DevOps Courses
            MockCourse(
                id=5, title="Docker Containerization", provider="CloudMaster",
                description="Master Docker containers and orchestration",
                skills_taught=["Docker", "Containerization", "Docker Compose"],
                difficulty_level="intermediate", duration_hours=35, rating=4.5, price=119.0,
                category="DevOps"
            ),
            MockCourse(
                id=6, title="Kubernetes Orchestration", provider="CloudMaster",
                description="Advanced Kubernetes deployment and management",
                skills_taught=["Kubernetes", "Container Orchestration", "Helm"],
                difficulty_level="advanced", duration_hours=45, rating=4.8, price=179.0,
                category="DevOps"
            ),
            
            # Data Science Courses
            MockCourse(
                id=7, title="Machine Learning Basics", provider="AILearn",
                description="Introduction to machine learning algorithms",
                skills_taught=["Machine Learning", "Python", "Scikit-learn", "Statistics"],
                difficulty_level="beginner", duration_hours=40, rating=4.6, price=139.0,
                category="Data Science"
            ),
            MockCourse(
                id=8, title="Deep Learning with TensorFlow", provider="AILearn",
                description="Advanced deep learning and neural networks",
                skills_taught=["TensorFlow", "Deep Learning", "Neural Networks", "CNN"],
                difficulty_level="advanced", duration_hours=60, rating=4.7, price=199.0,
                category="Data Science"
            )
        ]
    
    async def _generate_course_recommendations(self, user: Dict[str, Any]) -> List[CourseRecommendation]:
        """Generate course recommendations for a user"""
        recommendations = []
        
        current_skills = set(skill.lower() for skill in user["current_skills"])
        target_skills = set(skill.lower() for skill in user["target_skills"])
        skill_gaps = target_skills - current_skills
        
        for course in self.test_courses:
            # Calculate relevance score
            course_skills = set(skill.lower() for skill in course.skills_taught)
            skill_overlap = course_skills.intersection(skill_gaps)
            
            if skill_overlap:
                # Base relevance on skill overlap
                relevance_score = len(skill_overlap) / len(course_skills) * 100
                
                # Adjust for difficulty level match
                difficulty_bonus = self._calculate_difficulty_bonus(user["experience_level"], course.difficulty_level)
                relevance_score += difficulty_bonus
                
                # Adjust for course rating
                rating_bonus = (course.rating - 4.0) * 10  # Bonus for high-rated courses
                relevance_score += rating_bonus
                
                # Cap at 100
                relevance_score = min(relevance_score, 100.0)
                
                if relevance_score >= 50:  # Minimum threshold
                    recommendation = CourseRecommendation(
                        course=course,
                        relevance_score=relevance_score,
                        skill_gap_addressed=list(skill_overlap),
                        learning_path_position=len(recommendations) + 1,
                        estimated_completion_time=course.duration_hours
                    )
                    recommendations.append(recommendation)
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top 5 recommendations
        return recommendations[:5]
    
    async def _analyze_skill_gaps(self, current_skills: List[str], target_role: str) -> List[str]:
        """Analyze skill gaps for a target role"""
        # Mock skill requirements for different roles
        role_requirements = {
            "Data Scientist": ["Machine Learning", "Statistics", "Python", "Pandas", "NumPy", "SQL"],
            "Full Stack Developer": ["React", "Node.js", "Database Design", "API Development", "JavaScript", "HTML", "CSS"],
            "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Monitoring"]
        }
        
        required_skills = set(role_requirements.get(target_role, []))
        current_skills_set = set(current_skills)
        
        skill_gaps = required_skills - current_skills_set
        return list(skill_gaps)
    
    async def _create_learning_path(self, user_level: str, target_skills: List[str]) -> List[MockCourse]:
        """Create a learning path for target skills"""
        learning_path = []
        
        # Filter courses by target skills
        relevant_courses = []
        for course in self.test_courses:
            course_skills = set(skill.lower() for skill in course.skills_taught)
            target_skills_lower = set(skill.lower() for skill in target_skills)
            
            if course_skills.intersection(target_skills_lower):
                relevant_courses.append(course)
        
        # Sort by difficulty level (beginner -> intermediate -> advanced)
        difficulty_order = {"beginner": 1, "intermediate": 2, "advanced": 3}
        relevant_courses.sort(key=lambda c: difficulty_order.get(c.difficulty_level, 2))
        
        # Select courses based on user level
        if user_level == "beginner":
            # Start with beginner courses, add some intermediate
            learning_path = [c for c in relevant_courses if c.difficulty_level in ["beginner", "intermediate"]][:4]
        elif user_level == "intermediate":
            # Focus on intermediate and advanced courses
            learning_path = [c for c in relevant_courses if c.difficulty_level in ["intermediate", "advanced"]][:3]
        else:  # advanced
            # Focus on advanced courses
            learning_path = [c for c in relevant_courses if c.difficulty_level == "advanced"][:2]
        
        return learning_path
    
    def _calculate_difficulty_bonus(self, user_level: str, course_level: str) -> float:
        """Calculate difficulty matching bonus"""
        level_mapping = {"beginner": 1, "intermediate": 2, "advanced": 3}
        user_num = level_mapping.get(user_level, 2)
        course_num = level_mapping.get(course_level, 2)
        
        # Perfect match gets 10 points, adjacent levels get 5, others get 0
        diff = abs(user_num - course_num)
        if diff == 0:
            return 10.0
        elif diff == 1:
            return 5.0
        else:
            return 0.0
    
    async def _test_recommendation_relevance(self) -> Dict[str, Any]:
        """Test recommendation relevance"""
        try:
            # Mock user with specific needs
            test_user = {
                "current_skills": ["HTML", "CSS"],
                "target_skills": ["React", "JavaScript"],
                "experience_level": "beginner"
            }
            
            recommendations = await self._generate_course_recommendations(test_user)
            
            # Check if recommendations are relevant
            relevant_count = 0
            for rec in recommendations:
                course_skills = [skill.lower() for skill in rec.course.skills_taught]
                if any(skill in course_skills for skill in ["react", "javascript"]):
                    relevant_count += 1
            
            relevance_rate = relevant_count / len(recommendations) if recommendations else 0
            
            return {
                "test_name": "recommendation_relevance",
                "success": relevance_rate >= 0.8,  # 80% relevance threshold
                "relevance_rate": relevance_rate,
                "total_recommendations": len(recommendations),
                "relevant_recommendations": relevant_count
            }
            
        except Exception as e:
            return {
                "test_name": "recommendation_relevance",
                "success": False,
                "error": str(e)
            }
    
    async def _test_difficulty_progression(self) -> Dict[str, Any]:
        """Test difficulty progression in recommendations"""
        try:
            # Create learning path for beginner
            learning_path = await self._create_learning_path("beginner", ["React", "Node.js"])
            
            # Check if difficulty progresses appropriately
            difficulty_levels = [course.difficulty_level for course in learning_path]
            
            # Should start with beginner courses
            starts_with_beginner = difficulty_levels[0] == "beginner" if difficulty_levels else False
            
            # Should not jump from beginner to advanced without intermediate
            valid_progression = True
            for i in range(len(difficulty_levels) - 1):
                current = difficulty_levels[i]
                next_level = difficulty_levels[i + 1]
                
                if current == "beginner" and next_level == "advanced":
                    valid_progression = False
                    break
            
            return {
                "test_name": "difficulty_progression",
                "success": starts_with_beginner and valid_progression,
                "starts_with_beginner": starts_with_beginner,
                "valid_progression": valid_progression,
                "difficulty_sequence": difficulty_levels
            }
            
        except Exception as e:
            return {
                "test_name": "difficulty_progression",
                "success": False,
                "error": str(e)
            }
    
    async def _test_skill_coverage(self) -> Dict[str, Any]:
        """Test skill coverage in recommendations"""
        try:
            target_skills = ["React", "Node.js", "Docker"]
            learning_path = await self._create_learning_path("intermediate", target_skills)
            
            # Check skill coverage
            covered_skills = set()
            for course in learning_path:
                covered_skills.update(skill.lower() for skill in course.skills_taught)
            
            target_skills_lower = set(skill.lower() for skill in target_skills)
            coverage_rate = len(target_skills_lower.intersection(covered_skills)) / len(target_skills_lower)
            
            return {
                "test_name": "skill_coverage",
                "success": coverage_rate >= 0.8,  # 80% coverage threshold
                "coverage_rate": coverage_rate,
                "target_skills": len(target_skills),
                "covered_skills": len(target_skills_lower.intersection(covered_skills))
            }
            
        except Exception as e:
            return {
                "test_name": "skill_coverage",
                "success": False,
                "error": str(e)
            }
    
    async def _test_duration_estimation(self) -> Dict[str, Any]:
        """Test duration estimation accuracy"""
        try:
            learning_path = await self._create_learning_path("intermediate", ["Machine Learning"])
            
            # Calculate total duration
            total_duration = sum(course.duration_hours for course in learning_path)
            
            # Check if duration is reasonable (between 20-200 hours for a learning path)
            reasonable_duration = 20 <= total_duration <= 200
            
            # Check if individual course durations are reasonable (5-100 hours per course)
            reasonable_individual = all(5 <= course.duration_hours <= 100 for course in learning_path)
            
            return {
                "test_name": "duration_estimation",
                "success": reasonable_duration and reasonable_individual,
                "total_duration": total_duration,
                "reasonable_total": reasonable_duration,
                "reasonable_individual": reasonable_individual,
                "course_count": len(learning_path)
            }
            
        except Exception as e:
            return {
                "test_name": "duration_estimation",
                "success": False,
                "error": str(e)
            }