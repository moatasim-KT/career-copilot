from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import Counter

from ..models.user import User
from ..models.job import Job

class SkillGapAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def analyze_skill_gaps(self, user: User) -> Dict[str, Any]:
        """
        Analyzes skill gaps for a user based on their tracked jobs.
        - Aggregates all tech_stack arrays from user jobs.
        - Counts frequency of each skill.
        - Identifies skills not in user's profile.
        - Calculates skill coverage percentage.
        - Generates top 5 learning recommendations.
        """
        user_skills = set(s.lower() for s in user.skills) if user.skills else set()

        # Aggregate all tech_stack from user's jobs
        all_job_tech_stacks = []
        for job in user.jobs: # Assuming user.jobs is loaded via relationship
            if job.tech_stack:
                all_job_tech_stacks.extend([s.lower() for s in job.tech_stack])

        skill_frequency = Counter(all_job_tech_stacks)

        # Identify missing skills
        missing_skills = {}
        for skill, count in skill_frequency.items():
            if skill not in user_skills:
                missing_skills[skill] = count
        
        # Sort missing skills by frequency (most in-demand first)
        sorted_missing_skills = sorted(missing_skills.items(), key=lambda item: item[1], reverse=True)

        # Calculate skill coverage percentage
        total_market_skills = len(skill_frequency) # Total unique skills in jobs
        if total_market_skills == 0:
            skill_coverage_percentage = 100.0 # No jobs, so no gaps
        else:
            covered_skills_count = len(user_skills.intersection(skill_frequency.keys()))
            skill_coverage_percentage = (covered_skills_count / total_market_skills) * 100

        # Generate top 5 learning recommendations
        learning_recommendations = [
            f"Learn {skill.capitalize()} (appears in {count} relevant jobs)"
            for skill, count in sorted_missing_skills[:5]
        ]

        return {
            "user_skills": list(user_skills),
            "missing_skills": dict(sorted_missing_skills),
            "top_market_skills": dict(skill_frequency.most_common(5)),
            "skill_coverage_percentage": round(skill_coverage_percentage, 2),
            "learning_recommendations": learning_recommendations,
            "total_jobs_analyzed": len(user.jobs)
        }