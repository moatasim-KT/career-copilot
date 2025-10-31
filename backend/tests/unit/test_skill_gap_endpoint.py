#!/usr/bin/env python3
"""
Test script for skill gap analysis endpoint
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.models.user import User
from app.models.job import Job
from unittest.mock import Mock


def test_skill_gap_analyzer():
	"""Test the SkillGapAnalyzer service directly"""
	# Mock database session
	mock_db = Mock()

	# Create test user with skills
	test_user = User()
	test_user.id = 1
	test_user.username = "test_user"
	test_user.skills = ["Python", "FastAPI", "SQL"]

	# Create test jobs with tech stacks
	job1 = Job()
	job1.id = 1
	job1.company = "Tech Corp"
	job1.title = "Backend Developer"
	job1.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Docker"]

	job2 = Job()
	job2.id = 2
	job2.company = "Data Inc"
	job2.title = "Data Engineer"
	job2.tech_stack = ["Python", "Pandas", "Spark", "Kafka"]

	job3 = Job()
	job3.id = 3
	job3.company = "Web Solutions"
	job3.title = "Full Stack Developer"
	job3.tech_stack = ["JavaScript", "React", "Node.js", "MongoDB"]

	# Set up user jobs relationship
	test_user.jobs = [job1, job2, job3]

	# Initialize analyzer
	analyzer = SkillGapAnalyzer(db=mock_db)

	# Run analysis
	result = analyzer.analyze_skill_gaps(test_user)

	# Verify results
	assert "python" in result["user_skills"], "Python should be in user skills"
	assert "fastapi" in result["user_skills"], "FastAPI should be in user skills"
	assert "sql" in result["user_skills"], "SQL should be in user skills"

	# Check for expected missing skills
	expected_missing = ["docker", "pandas", "spark", "kafka", "javascript", "react", "node.js", "mongodb", "postgresql"]
	for skill in expected_missing:
		assert skill in result["missing_skills"], f"Correctly identified missing skill: {skill}"

	# Verify learning recommendations format
	assert len(result["learning_recommendations"]) > 0
	assert result["total_jobs_analyzed"] == 3
	assert result["skill_coverage_percentage"] == 18.18


def test_api_endpoint_structure():
	"""Test that the API endpoint structure is correct"""
	# Import the endpoint
	from app.api.v1.skill_gap import router

	# Check router configuration
	assert router.tags == ["skill-gap"]

	# Check if endpoint is properly decorated
	routes = router.routes
	skill_gap_route = None
	for route in routes:
		if hasattr(route, "path") and route.path == "/api/v1/skill-gap":
			skill_gap_route = route
			break

	assert skill_gap_route is not None, "/api/v1/skill-gap endpoint not found in router"
	assert "GET" in skill_gap_route.methods
