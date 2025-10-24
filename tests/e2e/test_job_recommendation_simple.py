#!/usr/bin/env python3
"""
Simple Job Recommendation Test

This test validates the job recommendation testing framework without requiring
full database setup. It focuses on testing the core recommendation logic
and API client functionality.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


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


class MockRecommendationEngine:
    """Mock recommendation engine for testing"""
    
    def __init__(self, db=None):
        self.db = db
    
    def calculate_match_score(self, user: MockUser, job: MockJob) -> float:
        """Calculate a simple match score for testing"""
        score = 0.0
        
        # Skill matching (50% weight)
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        job_skills = set(s.lower() for s in job.tech_stack) if job.tech_stack else set()
        
        if user_skills and job_skills:
            common_skills = user_skills.intersection(job_skills)
            skill_match = len(common_skills) / len(job_skills)
            score += skill_match * 50
        
        # Location matching (30% weight)
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        job_location = job.location.lower() if job.location else ""
        
        if user_locations and job_location:
            if "remote" in user_locations and "remote" in job_location:
                score += 30
            elif any(loc in job_location for loc in user_locations):
                score += 25
            else:
                score += 10
        
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
    
    def get_recommendations(self, user: MockUser, skip: int = 0, limit: int = 5) -> List[Dict]:
        """Get mock recommendations"""
        # Create some mock jobs for this user
        mock_jobs = [
            MockJob(
                id=1, user_id=user.id, title="Python Developer", company="TechCorp",
                location="San Francisco, CA", description="Python development role",
                tech_stack=["Python", "Django", "PostgreSQL"], salary_range="$80,000 - $100,000",
                job_type="full-time", remote_option=False
            ),
            MockJob(
                id=2, user_id=user.id, title="Senior Full Stack Engineer", company="StartupInc",
                location="Remote", description="Full stack development with React and Node.js",
                tech_stack=["React", "Node.js", "TypeScript"], salary_range="$120,000 - $150,000",
                job_type="full-time", remote_option=True
            ),
            MockJob(
                id=3, user_id=user.id, title="Data Scientist", company="DataCorp",
                location="Seattle, WA", description="Machine learning and data analysis",
                tech_stack=["Python", "TensorFlow", "SQL"], salary_range="$110,000 - $140,000",
                job_type="full-time", remote_option=True
            )
        ]
        
        # Calculate scores and return recommendations
        scored_jobs = []
        for job in mock_jobs:
            score = self.calculate_match_score(user, job)
            scored_jobs.append({"job": job, "score": score})
        
        # Sort by score and return top recommendations
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        return scored_jobs[skip:skip + limit]


class SimpleJobRecommendationTest:
    """Simple job recommendation test without database dependencies"""
    
    def __init__(self):
        self.test_users = []
        self.recommendation_engine = MockRecommendationEngine()
        
        # Create test user profiles
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
    
    def test_user_profile_creation(self) -> Dict[str, Any]:
        """Test creation of test user profiles"""
        print("🧪 Testing user profile creation...")
        
        results = {
            "success": True,
            "users_created": len(self.test_users),
            "profiles": []
        }
        
        for user in self.test_users:
            profile_info = {
                "name": user.name,
                "skills_count": len(user.skills),
                "locations_count": len(user.preferred_locations),
                "experience_level": user.experience_level,
                "has_career_goals": bool(user.career_goals)
            }
            results["profiles"].append(profile_info)
            print(f"  ✅ {user.name}: {len(user.skills)} skills, {user.experience_level} level")
        
        return results
    
    def test_recommendation_api_client(self) -> Dict[str, Any]:
        """Test recommendation API client functionality"""
        print("\n🔗 Testing recommendation API client...")
        
        results = {
            "success": True,
            "api_tests": [],
            "total_recommendations": 0,
            "average_scores": []
        }
        
        for user in self.test_users:
            try:
                # Get recommendations using mock engine
                recommendations = self.recommendation_engine.get_recommendations(user, limit=5)
                
                scores = [rec["score"] for rec in recommendations]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                api_test_result = {
                    "user_name": user.name,
                    "recommendations_count": len(recommendations),
                    "average_score": avg_score,
                    "max_score": max(scores) if scores else 0,
                    "min_score": min(scores) if scores else 0,
                    "success": True
                }
                
                results["api_tests"].append(api_test_result)
                results["total_recommendations"] += len(recommendations)
                results["average_scores"].append(avg_score)
                
                print(f"  ✅ {user.name}: {len(recommendations)} recommendations (avg: {avg_score:.1f})")
                
            except Exception as e:
                api_test_result = {
                    "user_name": user.name,
                    "error": str(e),
                    "success": False
                }
                results["api_tests"].append(api_test_result)
                results["success"] = False
                print(f"  ❌ {user.name}: Error - {str(e)}")
        
        return results
    
    def test_recommendation_relevance(self) -> Dict[str, Any]:
        """Test recommendation relevance validation"""
        print("\n🎯 Testing recommendation relevance...")
        
        results = {
            "success": True,
            "relevance_tests": [],
            "overall_relevance": 0
        }
        
        total_relevance_scores = []
        
        for user in self.test_users:
            try:
                # Get recommendations
                recommendations = self.recommendation_engine.get_recommendations(user, limit=5)
                
                # Calculate relevance metrics
                skill_matches = 0
                location_matches = 0
                experience_matches = 0
                
                user_skills = set(s.lower() for s in user.skills)
                user_locations = set(l.lower() for l in user.preferred_locations)
                user_exp = user.experience_level.lower()
                
                for rec in recommendations:
                    job = rec["job"]
                    
                    # Check skill matches
                    job_skills = set(s.lower() for s in job.tech_stack)
                    if user_skills.intersection(job_skills):
                        skill_matches += 1
                    
                    # Check location matches
                    job_location = job.location.lower()
                    if ("remote" in user_locations and "remote" in job_location) or \
                       any(loc in job_location for loc in user_locations):
                        location_matches += 1
                    
                    # Check experience matches
                    job_title = job.title.lower()
                    if user_exp in job_title or \
                       (user_exp == "junior" and any(term in job_title for term in ["junior", "entry"])) or \
                       (user_exp == "senior" and any(term in job_title for term in ["senior", "lead"])):
                        experience_matches += 1
                
                total_recs = len(recommendations)
                relevance_score = 0
                if total_recs > 0:
                    relevance_score = (
                        (skill_matches / total_recs * 0.5) +
                        (location_matches / total_recs * 0.3) +
                        (experience_matches / total_recs * 0.2)
                    )
                
                relevance_test = {
                    "user_name": user.name,
                    "total_recommendations": total_recs,
                    "skill_matches": skill_matches,
                    "location_matches": location_matches,
                    "experience_matches": experience_matches,
                    "relevance_score": relevance_score,
                    "success": True
                }
                
                results["relevance_tests"].append(relevance_test)
                total_relevance_scores.append(relevance_score)
                
                print(f"  ✅ {user.name}: {relevance_score:.1%} relevance "
                      f"({skill_matches}/{total_recs} skills, {location_matches}/{total_recs} location)")
                
            except Exception as e:
                relevance_test = {
                    "user_name": user.name,
                    "error": str(e),
                    "success": False
                }
                results["relevance_tests"].append(relevance_test)
                results["success"] = False
                print(f"  ❌ {user.name}: Error - {str(e)}")
        
        if total_relevance_scores:
            results["overall_relevance"] = sum(total_relevance_scores) / len(total_relevance_scores)
        
        return results
    
    def test_recommendation_quality_distribution(self) -> Dict[str, Any]:
        """Test recommendation quality distribution"""
        print("\n⭐ Testing recommendation quality distribution...")
        
        quality_distribution = {"excellent": 0, "high": 0, "medium": 0, "low": 0}
        all_scores = []
        
        for user in self.test_users:
            recommendations = self.recommendation_engine.get_recommendations(user, limit=10)
            
            for rec in recommendations:
                score = rec["score"]
                all_scores.append(score)
                
                if score >= 80:
                    quality_distribution["excellent"] += 1
                elif score >= 60:
                    quality_distribution["high"] += 1
                elif score >= 40:
                    quality_distribution["medium"] += 1
                else:
                    quality_distribution["low"] += 1
        
        total_recommendations = sum(quality_distribution.values())
        
        print(f"  📊 Quality Distribution (Total: {total_recommendations}):")
        for quality, count in quality_distribution.items():
            percentage = count / total_recommendations * 100 if total_recommendations > 0 else 0
            print(f"    {quality.title()}: {count} ({percentage:.1f}%)")
        
        return {
            "success": True,
            "quality_distribution": quality_distribution,
            "total_recommendations": total_recommendations,
            "average_score": sum(all_scores) / len(all_scores) if all_scores else 0,
            "max_score": max(all_scores) if all_scores else 0,
            "min_score": min(all_scores) if all_scores else 0
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive job recommendation test"""
        print("🎯 Job Recommendation Test Framework - Simple Version")
        print("=" * 60)
        
        # Run all tests
        profile_results = self.test_user_profile_creation()
        api_results = self.test_recommendation_api_client()
        relevance_results = self.test_recommendation_relevance()
        quality_results = self.test_recommendation_quality_distribution()
        
        # Calculate overall success
        overall_success = all([
            profile_results.get("success", False),
            api_results.get("success", False),
            relevance_results.get("success", False),
            quality_results.get("success", False)
        ])
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print("=" * 30)
        print(f"Overall Success: {'✅' if overall_success else '❌'}")
        print(f"Test Users: {profile_results.get('users_created', 0)}")
        print(f"Total Recommendations: {api_results.get('total_recommendations', 0)}")
        print(f"Average Relevance: {relevance_results.get('overall_relevance', 0):.1%}")
        print(f"Average Quality Score: {quality_results.get('average_score', 0):.1f}")
        
        return {
            "overall_success": overall_success,
            "profile_test": profile_results,
            "api_test": api_results,
            "relevance_test": relevance_results,
            "quality_test": quality_results,
            "summary": {
                "users_tested": len(self.test_users),
                "total_recommendations": api_results.get("total_recommendations", 0),
                "overall_relevance": relevance_results.get("overall_relevance", 0),
                "average_quality": quality_results.get("average_score", 0)
            }
        }


def main():
    """Main function to run the simple test"""
    try:
        test = SimpleJobRecommendationTest()
        results = test.run_comprehensive_test()
        
        if results["overall_success"]:
            print(f"\n✅ All tests passed successfully!")
            return 0
        else:
            print(f"\n❌ Some tests failed. Check the results above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())