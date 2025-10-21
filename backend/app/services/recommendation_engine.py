from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter

from ..models.user import User
from ..models.job import Job

class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.experience_levels = {
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "staff": 5,
            "principal": 6
        }

    def calculate_match_score(self, user: User, job: Job) -> float:
        """
        Calculates a match score between a user and a job based on:
        - Tech stack (50% weight)
        - Location (30% weight)
        - Experience level (20% weight)
        Scores are capped at 100.
        """
        score = 0.0

        # 1. Tech Stack Match (50% weight)
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()
        job_tech_stack = set(t.lower() for t in job.tech_stack) if job.tech_stack else set()

        if user_skills and job_tech_stack:
            common_skills = user_skills.intersection(job_tech_stack)
            skill_match_percentage = len(common_skills) / len(job_tech_stack)
            score += skill_match_percentage * 50

        # 2. Location Match (30% weight)
        user_locations = set(l.lower() for l in user.preferred_locations) if user.preferred_locations else set()
        job_location = job.location.lower() if job.location else ""

        if user_locations and job_location:
            if "remote" in user_locations and "remote" in job_location:
                score += 30  # Perfect remote match
            elif any(loc in job_location for loc in user_locations):
                score += 25  # Partial location match
            elif "remote" in user_locations and "remote" not in job_location:
                score += 10  # User prefers remote, job is not explicitly remote
            elif "remote" not in user_locations and "remote" in job_location:
                score += 10  # Job is remote, user does not prefer remote
            elif "remote" in user_locations and not job_location:
                score += 15 # User prefers remote, job has no location specified
            elif not user_locations and job_location:
                score += 5 # User has no location preference, job has location

        # 3. Experience Level Match (20% weight)
        user_exp = self.experience_levels.get(user.experience_level.lower(), 0) if user.experience_level else 0
        
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
                score += 20  # Perfect experience match
            elif abs(user_exp - job_exp) == 1:
                score += 10  # Close experience match
            else:
                score += 5   # Some experience match

        return min(score, 100.0) # Cap score at 100

    def get_recommendations(self, user: User, skip: int = 0, limit: int = 5) -> List[Dict]:
        """
        Queries jobs that have not been applied to by the user, calculates match scores,
        and returns top N recommendations.
        """
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

        # Sort by score descending
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)

        # Return top N recommendations with pagination
        return scored_jobs[skip:skip + limit]