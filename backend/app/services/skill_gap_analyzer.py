"""Skill Gap Analyzer for identifying user skill gaps based on job requirements."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class SkillGapAnalyzer:
	def __init__(self, db: Optional[Any] = None) -> None:
		"""Store an optional database session for downstream use."""
		self._db = db

	async def detect_gaps(self, user_id: int, current_skills: List[Any]) -> List[Dict[str, Any]]:
		"""Return an empty gap list until a real implementation is available."""
		return []

	def analyze_skill_gaps(self, user: Any) -> Dict[str, Any]:
		"""
		Analyze skill gaps for a user based on their jobs.

		Args:
			user: User object with skills and jobs attributes

		Returns:
			Dictionary containing:
			- user_skills: List of normalized user skills
			- missing_skills: List of skills the user doesn't have
			- top_market_skills: Top skills from the job market
			- skill_coverage_percentage: Percentage of required skills the user has
			- recommendations: List of skill recommendations
		"""
		# Normalize user skills to lowercase
		user_skills = [skill.lower() for skill in (user.skills or [])]

		# Extract all required skills from user's jobs
		required_skills = set()
		job_count = 0

		if hasattr(user, "jobs") and user.jobs:
			for job in user.jobs:
				job_count += 1
				if hasattr(job, "tech_stack") and job.tech_stack:
					for skill in job.tech_stack:
						required_skills.add(skill.lower())

		# Calculate missing skills
		missing_skills = sorted(list(required_skills - set(user_skills)))

		# Calculate skill coverage percentage
		if required_skills:
			coverage = (len(set(user_skills) & required_skills) / len(required_skills)) * 100
		else:
			coverage = 100.0 if user_skills else 0.0

		# Get top market skills (most frequently required)
		skill_frequency = {}
		if hasattr(user, "jobs") and user.jobs:
			for job in user.jobs:
				if hasattr(job, "tech_stack") and job.tech_stack:
					for skill in job.tech_stack:
						skill_lower = skill.lower()
						skill_frequency[skill_lower] = skill_frequency.get(skill_lower, 0) + 1

		# Sort skills by frequency and get top 10
		top_market_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
		top_market_skills = [skill for skill, _ in top_market_skills]

		# Generate recommendations (prioritize missing high-frequency skills)
		recommendations = []
		for skill in missing_skills[:5]:  # Top 5 missing skills
			freq = skill_frequency.get(skill, 1)
			priority = "high" if freq >= 2 else "medium"
			recommendations.append(f"Learn {skill} ({priority} priority) - appears in {freq} job(s)")

		return {
			"user_skills": user_skills,
			"missing_skills": missing_skills,
			"top_market_skills": top_market_skills,
			"skill_coverage_percentage": round(coverage, 2),
			"recommendations": recommendations,
		}
