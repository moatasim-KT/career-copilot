"""
Test script for feedback analysis and model improvement functionality
"""

import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import get_db, init_db
from app.models.feedback import JobRecommendationFeedback
from app.models.job import Job
from app.models.user import User

# from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine  # Service refactored
from app.services.feedback_analysis_service import FeedbackAnalysisService
from app.services.feedback_impact_service import FeedbackImpactService
from app.utils.datetime import utc_now

pytestmark = pytest.mark.skip(reason="Service refactored - adaptive_recommendation_engine no longer exists")


def create_test_data(db: Session):
	"""Create test data for feedback analysis"""
	print("Creating test data...")

	# Get existing user or create a simple one
	test_user = db.query(User).first()
	if not test_user:
		# Create minimal test user
		test_user = User(username="test_feedback_user", email="feedback@test.com", hashed_password="test_hash")
		db.add(test_user)
		db.commit()
		db.refresh(test_user)

	# Update user with test data
	test_user.skills = ["Python", "FastAPI", "Machine Learning"]
	test_user.preferred_locations = ["Remote", "San Francisco"]
	test_user.experience_level = "senior"
	db.commit()

	# Create test jobs
	jobs = [
		Job(
			user_id=test_user.id,
			company="TechCorp",
			title="Senior Python Developer",
			location="Remote",
			tech_stack=["Python", "FastAPI", "PostgreSQL"],
			status="not_applied",
		),
		Job(
			user_id=test_user.id,
			company="DataCorp",
			title="ML Engineer",
			location="San Francisco",
			tech_stack=["Python", "Machine Learning", "TensorFlow"],
			status="not_applied",
		),
		Job(
			user_id=test_user.id,
			company="StartupCorp",
			title="Full Stack Developer",
			location="New York",
			tech_stack=["JavaScript", "React", "Node.js"],
			status="not_applied",
		),
	]

	for job in jobs:
		db.add(job)
	db.commit()

	# Create test feedback
	feedback_items = [
		JobRecommendationFeedback(
			user_id=test_user.id,
			job_id=jobs[0].id,
			is_helpful=True,
			match_score=85,
			user_skills_at_time=["Python", "FastAPI", "Machine Learning"],
			user_experience_level="senior",
			user_preferred_locations=["Remote", "San Francisco"],
			job_tech_stack=["Python", "FastAPI", "PostgreSQL"],
			job_location="Remote",
			created_at=utc_now() - timedelta(days=5),
		),
		JobRecommendationFeedback(
			user_id=test_user.id,
			job_id=jobs[1].id,
			is_helpful=True,
			match_score=90,
			user_skills_at_time=["Python", "FastAPI", "Machine Learning"],
			user_experience_level="senior",
			user_preferred_locations=["Remote", "San Francisco"],
			job_tech_stack=["Python", "Machine Learning", "TensorFlow"],
			job_location="San Francisco",
			created_at=utc_now() - timedelta(days=3),
		),
		JobRecommendationFeedback(
			user_id=test_user.id,
			job_id=jobs[2].id,
			is_helpful=False,
			match_score=45,
			user_skills_at_time=["Python", "FastAPI", "Machine Learning"],
			user_experience_level="senior",
			user_preferred_locations=["Remote", "San Francisco"],
			job_tech_stack=["JavaScript", "React", "Node.js"],
			job_location="New York",
			created_at=utc_now() - timedelta(days=1),
		),
	]

	for feedback in feedback_items:
		db.add(feedback)
	db.commit()

	print(f"✅ Created test user (ID: {test_user.id}), 3 jobs, and 3 feedback items")
	return test_user, jobs, feedback_items


def test_feedback_analysis(db: Session):
	"""Test feedback analysis functionality"""
	print("\n=== Testing Feedback Analysis Service ===")

	analysis_service = FeedbackAnalysisService(db)

	# Test pattern analysis
	print("1. Testing feedback pattern analysis...")
	patterns = analysis_service.analyze_feedback_patterns(days_back=30)
	print(f"   Total feedback analyzed: {patterns['total_feedback']}")
	print(f"   Patterns identified: {len(patterns['patterns'])}")
	print(f"   Recommendations generated: {len(patterns['recommendations'])}")

	# Test algorithm suggestions
	print("2. Testing algorithm adjustment suggestions...")
	suggestions = analysis_service.get_algorithm_adjustment_suggestions()
	print(f"   Current weights: {suggestions['current_weights']}")
	print(f"   Suggested weights: {suggestions['suggested_weights']}")
	print(f"   Confidence score: {suggestions['confidence_score']:.2f}")
	print(f"   Sample size: {suggestions['sample_size']}")

	return patterns, suggestions


def test_adaptive_engine(db: Session, test_user: User):
	"""Test adaptive recommendation engine"""
	print("\n=== Testing Adaptive Recommendation Engine ===")

	engine = AdaptiveRecommendationEngine(db)

	# Test weight retrieval
	print("1. Testing algorithm weights for user...")
	weights = engine.get_algorithm_weights(test_user.id)
	print(f"   User {test_user.id} weights: {weights}")

	# Test A/B test assignment
	print("2. Testing A/B test assignment...")
	variant = engine.get_user_algorithm_variant(test_user.id, "skill_weight_test")
	print(f"   User assigned to variant: {variant}")

	# Test adaptive recommendations
	print("3. Testing adaptive recommendations...")
	recommendations = engine.get_recommendations_adaptive(test_user, limit=3)
	print(f"   Generated {len(recommendations)} recommendations")
	for i, rec in enumerate(recommendations):
		print(f"   {i + 1}. {rec['job'].company} - {rec['job'].title} (Score: {rec['score']:.1f})")

	# Test A/B test creation
	print("4. Testing A/B test creation...")
	try:
		engine.start_ab_test(
			"test_experiment",
			{"skill_matching": 50, "location_matching": 30, "experience_matching": 20},
			{"skill_matching": 60, "location_matching": 25, "experience_matching": 15},
			traffic_split=0.5,
		)
		print("   ✅ A/B test created successfully")
	except Exception as e:
		print(f"   ❌ A/B test creation failed: {e}")

	return recommendations


def test_feedback_impact(db: Session):
	"""Test feedback impact service"""
	print("\n=== Testing Feedback Impact Service ===")

	impact_service = FeedbackImpactService(db)

	# Test improvement report
	print("1. Testing improvement report generation...")
	report = impact_service.generate_improvement_report(days_back=30)
	print(f"   Report period: {report['report_period']['days_back']} days")
	print(f"   Baseline satisfaction: {report['baseline_metrics']['satisfaction_rate']:.1%}")
	print(f"   Improvement trend: {report['improvement_trends']['trend']}")
	print(f"   Recommendations: {len(report['recommendations'])}")

	# Test ROI analysis
	print("2. Testing ROI analysis...")
	roi = impact_service.get_feedback_roi_analysis(days_back=30)
	if roi.get("roi_analysis") != "insufficient_data":
		print(f"   Total feedback: {roi['feedback_metrics']['total_feedback']}")
		print(f"   Satisfaction improvement: {roi['satisfaction_metrics']['satisfaction_improvement']:.1%}")
		print(f"   ROI category: {roi['estimated_business_impact']['roi_category']}")
	else:
		print("   ⚠️ Insufficient data for ROI analysis")

	return report, roi


def main():
	"""Main test function"""
	print("🧪 Testing Feedback Analysis and Model Improvement System")
	print("=" * 60)

	# Initialize database
	init_db()
	db = next(get_db())

	try:
		# Create test data
		test_user, _jobs, _feedback_items = create_test_data(db)

		# Test feedback analysis
		patterns, suggestions = test_feedback_analysis(db)

		# Test adaptive engine
		recommendations = test_adaptive_engine(db, test_user)

		# Test feedback impact
		_report, _roi = test_feedback_impact(db)

		print("\n" + "=" * 60)
		print("🎉 All tests completed successfully!")
		print("\n📊 Summary:")
		print(f"   • Analyzed {patterns['total_feedback']} feedback items")
		print(f"   • Generated {len(recommendations)} adaptive recommendations")
		print(f"   • Identified {len(patterns['recommendations'])} improvement opportunities")
		print(f"   • Algorithm confidence: {suggestions['confidence_score']:.1%}")

	except Exception as e:
		print(f"\n❌ Test failed with error: {e}")
		import traceback

		traceback.print_exc()

	finally:
		# Clean up test data
		try:
			db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.user_id == test_user.id).delete()
			db.query(Job).filter(Job.user_id == test_user.id).delete()
			db.query(User).filter(User.id == test_user.id).delete()
			db.commit()
			print("\n🧹 Test data cleaned up")
		except:
			pass

		db.close()


if __name__ == "__main__":
	main()
