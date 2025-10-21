"""Job recommendation engine"""

from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.job import Job
from ..models.user import User


class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_match_score(self, user: User, job: Job) -> float:
        score = 0.0

        # 1. Tech Stack Match (50%)
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        job_tech_stack = set(t.lower() for t in job.tech_stack) if job.tech_stack else set()

        if user_skills and job_tech_stack:
            common_skills = user_skills.intersection(job_tech_stack)
            skill_match_percentage = len(common_skills) / len(job_tech_stack)
            score += skill_match_percentage * 0.50

        # 2. Location Match (30%)
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        job_location = job.location.lower() if job.location else ""

        if user_locations and job_location:
            if "remote" in user_locations and "remote" in job_location:
                score += 0.30
            elif any(loc in job_location for loc in user_locations):
                score += 0.30
            elif "remote" in user_locations and "remote" not in job_location:
                pass
            elif "remote" not in user_locations and "remote" in job_location:
                pass
        elif "remote" in user_locations and not job_location:
            score += 0.15
        elif not user_locations and job_location:
            score += 0.15

        # 3. Experience Level Match (20%)
        experience_levels = {"junior": 1, "mid": 2, "senior": 3, "lead": 4, "staff": 5, "principal": 6}
        user_exp = experience_levels.get(user.experience_level.lower(), 0) if user.experience_level else 0
        job_title_lower = job.title.lower()

        job_exp = 0
        if "junior" in job_title_lower: job_exp = 1
        elif "mid" in job_title_lower: job_exp = 2
        elif "senior" in job_title_lower: job_exp = 3
        elif "lead" in job_title_lower: job_exp = 4
        elif "staff" in job_title_lower: job_exp = 5
        elif "principal" in job_title_lower: job_exp = 6

        if user_exp > 0 and job_exp > 0:
            if user_exp == job_exp:
                score += 0.20
            elif abs(user_exp - job_exp) == 1:
                score += 0.10

        return min(round(score * 100), 100)
    
    def get_recommendations(self, user: User, skip: int = 0, limit: int = 5) -> List[Dict]:
        # Query only jobs with status not_applied for the current user
        jobs = self.db.query(Job).filter(
            Job.user_id == user.id,
            Job.status == "not_applied"
        ).all()

        # Calculate match score for each job
        scored_jobs = []
        for job in jobs:
            score = self.calculate_match_score(user, job)
            scored_jobs.append({
                "job": job,
                "score": score
            })

        # Sort by score descending and return top N
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        return scored_jobs[skip:skip + limit]
