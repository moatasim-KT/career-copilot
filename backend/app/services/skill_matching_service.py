"""
Skill Matching Service
Comprehensive skill extraction, matching, and recommendation service
"""

import logging
import re
from collections import Counter
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.utils.datetime import utc_now

logger = logging.getLogger(__name__)


# Common technical skills database
TECH_SKILLS = {
	# Programming Languages
	"python",
	"javascript",
	"typescript",
	"java",
	"c++",
	"c#",
	"go",
	"rust",
	"ruby",
	"php",
	"swift",
	"kotlin",
	"scala",
	"r",
	"matlab",
	"sql",
	"bash",
	"shell",
	"powershell",
	# Web Development
	"html",
	"css",
	"react",
	"angular",
	"vue",
	"svelte",
	"next.js",
	"nuxt.js",
	"gatsby",
	"node.js",
	"express",
	"fastapi",
	"django",
	"flask",
	"spring",
	"asp.net",
	"laravel",
	# Data Science & ML
	"pandas",
	"numpy",
	"scikit-learn",
	"tensorflow",
	"pytorch",
	"keras",
	"xgboost",
	"lightgbm",
	"catboost",
	"spacy",
	"nltk",
	"opencv",
	"matplotlib",
	"seaborn",
	"plotly",
	"jupyter",
	"tableau",
	"power bi",
	"looker",
	"spark",
	"hadoop",
	"airflow",
	# Databases
	"postgresql",
	"mysql",
	"mongodb",
	"redis",
	"elasticsearch",
	"cassandra",
	"dynamodb",
	"oracle",
	"mssql",
	"neo4j",
	"firebase",
	"supabase",
	# Cloud & DevOps
	"aws",
	"azure",
	"gcp",
	"google cloud",
	"docker",
	"kubernetes",
	"jenkins",
	"gitlab",
	"github actions",
	"terraform",
	"ansible",
	"ci/cd",
	"linux",
	"nginx",
	"apache",
	# Other Technical
	"git",
	"api",
	"rest",
	"graphql",
	"microservices",
	"agile",
	"scrum",
	"jira",
	"testing",
	"unit testing",
	"pytest",
	"jest",
	"selenium",
	"automation",
}

# Role-specific skill requirements
ROLE_SKILLS = {
	"data scientist": {
		"required": ["python", "sql", "statistics", "machine learning"],
		"preferred": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "jupyter", "git"],
		"nice_to_have": ["spark", "aws", "docker", "tableau", "r"],
	},
	"data analyst": {
		"required": ["sql", "excel", "statistics", "data visualization"],
		"preferred": ["python", "tableau", "power bi", "pandas", "numpy"],
		"nice_to_have": ["r", "looker", "google analytics", "aws"],
	},
	"ml engineer": {
		"required": ["python", "machine learning", "tensorflow", "pytorch"],
		"preferred": ["docker", "kubernetes", "mlops", "ci/cd", "git", "aws"],
		"nice_to_have": ["scala", "spark", "airflow", "kubeflow"],
	},
	"ai engineer": {
		"required": ["python", "deep learning", "neural networks", "tensorflow"],
		"preferred": ["pytorch", "nlp", "computer vision", "mlops", "docker"],
		"nice_to_have": ["transformers", "hugging face", "langchain", "openai"],
	},
	"software engineer": {
		"required": ["programming", "algorithms", "data structures", "git"],
		"preferred": ["python", "java", "javascript", "sql", "testing", "agile"],
		"nice_to_have": ["aws", "docker", "kubernetes", "ci/cd"],
	},
	"full stack developer": {
		"required": ["javascript", "html", "css", "backend", "frontend"],
		"preferred": ["react", "node.js", "sql", "git", "rest api"],
		"nice_to_have": ["typescript", "docker", "aws", "next.js", "mongodb"],
	},
}


class SkillMatchingService:
	"""Comprehensive skill matching and analysis service"""

	def __init__(self):
		"""Initialize the skill matching service"""
		self.tech_skills = TECH_SKILLS
		self.role_skills = ROLE_SKILLS
		logger.info("Skill matching service initialized")

	def match_skills(self, user_skills: List[str], job_requirements: List[str], job_title: Optional[str] = None) -> Dict[str, Any]:
		"""
		Match user skills against job requirements with detailed analysis

		Args:
		    user_skills: List of user's skills
		    job_requirements: List of required skills for job
		    job_title: Optional job title for role-specific matching

		Returns:
		    Detailed match results with score and skill categorization
		"""
		# Normalize skills (lowercase, strip whitespace)
		user_skills_norm = {skill.lower().strip() for skill in user_skills if skill}
		job_req_norm = {req.lower().strip() for req in job_requirements if req}

		# Calculate matches
		matched_skills = user_skills_norm & job_req_norm
		missing_skills = job_req_norm - user_skills_norm
		extra_skills = user_skills_norm - job_req_norm

		# Calculate match score
		if not job_req_norm:
			match_score = 1.0
		else:
			match_score = len(matched_skills) / len(job_req_norm)

		# Categorize missing skills by importance if job title provided
		skill_categories = self._categorize_missing_skills(missing_skills, job_title) if job_title else {}

		return {
			"match_score": round(match_score * 100, 2),
			"matched_skills": sorted(list(matched_skills)),
			"missing_skills": sorted(list(missing_skills)),
			"extra_skills": sorted(list(extra_skills)),
			"total_required": len(job_req_norm),
			"total_matched": len(matched_skills),
			"total_missing": len(missing_skills),
			"skill_categories": skill_categories,
			"recommendation": self._get_match_recommendation(match_score),
		}

	def extract_skills(self, text: str, include_soft_skills: bool = False) -> List[str]:
		"""
		Extract technical skills from text (resume, job description, etc.)

		Args:
		    text: Text to extract skills from
		    include_soft_skills: Whether to include soft skills

		Returns:
		    List of extracted skills
		"""
		if not text:
			return []

		text_lower = text.lower()
		extracted = set()

		# Extract technical skills
		for skill in self.tech_skills:
			# Use word boundaries for better matching
			pattern = r"\b" + re.escape(skill) + r"\b"
			if re.search(pattern, text_lower):
				extracted.add(skill)

		# Extract soft skills if requested
		if include_soft_skills:
			soft_skills = {
				"leadership",
				"communication",
				"teamwork",
				"problem solving",
				"critical thinking",
				"time management",
				"adaptability",
				"creativity",
				"attention to detail",
				"collaboration",
				"analytical",
				"strategic thinking",
			}
			for skill in soft_skills:
				pattern = r"\b" + re.escape(skill) + r"\b"
				if re.search(pattern, text_lower):
					extracted.add(skill)

		return sorted(list(extracted))

	def suggest_skills(self, current_skills: List[str], target_role: str, limit: int = 10) -> List[Dict[str, Any]]:
		"""
		Suggest additional skills to learn based on target role

		Args:
		    current_skills: User's current skills
		    target_role: Target job role
		    limit: Maximum number of suggestions

		Returns:
		    List of suggested skills with priority and reasoning
		"""
		current_skills_norm = {skill.lower().strip() for skill in current_skills if skill}
		target_role_lower = target_role.lower()

		# Find matching role profile
		role_profile = None
		for role, profile in self.role_skills.items():
			if role in target_role_lower:
				role_profile = profile
				break

		if not role_profile:
			# Default suggestions for unknown roles
			common_skills = ["python", "sql", "git", "docker", "aws", "testing"]
			suggestions = []
			for skill in common_skills:
				if skill not in current_skills_norm:
					suggestions.append({"skill": skill, "priority": "medium", "category": "general", "reason": "Widely used across technical roles"})
			return suggestions[:limit]

		suggestions = []

		# Required skills (highest priority)
		for skill in role_profile.get("required", []):
			if skill not in current_skills_norm:
				suggestions.append({"skill": skill, "priority": "high", "category": "required", "reason": f"Essential for {target_role} roles"})

		# Preferred skills (medium priority)
		for skill in role_profile.get("preferred", []):
			if skill not in current_skills_norm:
				suggestions.append(
					{"skill": skill, "priority": "medium", "category": "preferred", "reason": f"Commonly requested for {target_role} positions"}
				)

		# Nice-to-have skills (low priority)
		for skill in role_profile.get("nice_to_have", []):
			if skill not in current_skills_norm:
				suggestions.append(
					{"skill": skill, "priority": "low", "category": "nice_to_have", "reason": f"Gives you an edge in {target_role} applications"}
				)

		return suggestions[:limit]

	def calculate_skill_gap(self, user_id: int, job_id: int, db: Session) -> Dict[str, Any]:
		"""
		Calculate skill gap between user and specific job

		Args:
		    user_id: User ID
		    job_id: Job ID
		    db: Database session

		Returns:
		    Detailed skill gap analysis
		"""
		try:
			from app.models.job import Job
			from app.models.user import User

			user = db.query(User).filter(User.id == user_id).first()
			job = db.query(Job).filter(Job.id == job_id).first()

			if not user or not job:
				return {"error": "User or job not found"}

			user_skills = list(user.skills or [])
			job_skills = self.extract_skills(f"{job.title} {job.description} {job.requirements or ''}")

			match_result = self.match_skills(user_skills=user_skills, job_requirements=job_skills, job_title=job.title)

			# Add learning path
			learning_path = self.suggest_skills(current_skills=user_skills, target_role=job.title, limit=5)

			return {**match_result, "learning_path": learning_path, "job_title": job.title, "job_company": job.company}

		except Exception as e:
			logger.error(f"Error calculating skill gap: {e}")
			return {"error": str(e)}

	def _categorize_missing_skills(self, missing_skills: Set[str], job_title: Optional[str]) -> Dict[str, List[str]]:
		"""Categorize missing skills by importance"""
		if not job_title:
			return {}

		job_title_lower = job_title.lower()
		role_profile = None

		for role, profile in self.role_skills.items():
			if role in job_title_lower:
				role_profile = profile
				break

		if not role_profile:
			return {"other": list(missing_skills)}

		categorized = {"critical": [], "important": [], "nice_to_have": []}

		for skill in missing_skills:
			if skill in role_profile.get("required", []):
				categorized["critical"].append(skill)
			elif skill in role_profile.get("preferred", []):
				categorized["important"].append(skill)
			elif skill in role_profile.get("nice_to_have", []):
				categorized["nice_to_have"].append(skill)
			else:
				if "other" not in categorized:
					categorized["other"] = []
				categorized["other"].append(skill)

		# Remove empty categories
		return {k: v for k, v in categorized.items() if v}

	def _get_match_recommendation(self, match_score: float) -> str:
		"""Get recommendation based on match score"""
		if match_score >= 0.8:
			return "Excellent match! You meet most requirements. Apply with confidence."
		elif match_score >= 0.6:
			return "Good match! You meet many requirements. Consider applying."
		elif match_score >= 0.4:
			return "Moderate match. Review missing skills before applying."
		else:
			return "Low match. Consider building more relevant skills first."

	def analyze_skill_trends(self, db: Session, role: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
		"""
		Analyze trending skills from recent job postings

		Args:
		    db: Database session
		    role: Optional specific role to analyze
		    days: Number of days to look back

		Returns:
		    Skill trend analysis
		"""
		try:
			from app.models.job import Job

			# Query recent jobs
			cutoff_date = utc_now() - timedelta(days=days)
			query = db.query(Job).filter(Job.created_at >= cutoff_date)

			if role:
				query = query.filter(Job.title.ilike(f"%{role}%"))

			jobs = query.all()

			# Extract and count skills
			all_skills = []
			for job in jobs:
				text = f"{job.title} {job.description} {job.requirements or ''}"
				skills = self.extract_skills(text)
				all_skills.extend(skills)

			# Count skill frequencies
			skill_counts = Counter(all_skills)

			return {
				"trending_skills": [
					{"skill": skill, "count": count, "percentage": round(count / len(jobs) * 100, 1)} for skill, count in skill_counts.most_common(20)
				],
				"total_jobs_analyzed": len(jobs),
				"analysis_period_days": days,
				"role_filter": role or "all roles",
			}

		except Exception as e:
			logger.error(f"Error analyzing skill trends: {e}")
			return {"error": str(e)}


# Global instance
_skill_matching_service_instance: Optional[SkillMatchingService] = None


def get_skill_matching_service() -> SkillMatchingService:
	"""Get or create skill matching service instance"""
	global _skill_matching_service_instance
	if _skill_matching_service_instance is None:
		_skill_matching_service_instance = SkillMatchingService()
	return _skill_matching_service_instance


logger.info("Skill matching service module initialized")
