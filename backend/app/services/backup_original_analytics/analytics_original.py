from sqlalchemy.orm import Session
import json
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy import func

from ..models.user import User
from ..models.job import Job
from ..models.application import Application
from ..utils.redis_client import redis_client


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_analytics(self, user: User) -> Dict[str, Any]:
        """
        Calculates various analytics metrics for a user.
        """
        # Basic counts
        total_jobs = self.db.query(Job).filter(Job.user_id == user.id).count()
        total_applications = (
            self.db.query(Application).filter(Application.user_id == user.id).count()
        )

        # Status-based counts
        pending_applications = (
            self.db.query(Application)
            .filter(
                Application.user_id == user.id,
                Application.status.in_(["interested", "applied"]),
            )
            .count()
        )

        interviews_scheduled = (
            self.db.query(Application)
            .filter(Application.user_id == user.id, Application.status == "interview")
            .count()
        )

        offers_received = (
            self.db.query(Application)
            .filter(
                Application.user_id == user.id,
                Application.status.in_(["offer", "accepted"]),
            )
            .count()
        )

        rejections_received = (
            self.db.query(Application)
            .filter(Application.user_id == user.id, Application.status == "rejected")
            .count()
        )

        # Acceptance rate
        accepted_applications = (
            self.db.query(Application)
            .filter(Application.user_id == user.id, Application.status == "accepted")
            .count()
        )
        acceptance_rate = (
            (accepted_applications / offers_received * 100)
            if offers_received > 0
            else 0.0
        )

        # Daily, weekly, monthly applications
        today = datetime.utcnow().date()
        daily_applications_today = (
            self.db.query(Application)
            .filter(Application.user_id == user.id, Application.applied_date == today)
            .count()
        )

        one_week_ago = today - timedelta(days=7)
        weekly_applications = (
            self.db.query(Application)
            .filter(
                Application.user_id == user.id, Application.applied_date >= one_week_ago
            )
            .count()
        )

        one_month_ago = today - timedelta(days=30)  # Approximation for a month
        monthly_applications = (
            self.db.query(Application)
            .filter(
                Application.user_id == user.id,
                Application.applied_date >= one_month_ago,
            )
            .count()
        )

        # Daily application goal and progress
        daily_application_goal = (
            user.daily_application_goal
            if user.daily_application_goal is not None
            else 10
        )
        daily_goal_progress = (
            (daily_applications_today / daily_application_goal * 100)
            if daily_application_goal > 0
            else 0.0
        )
        daily_goal_progress = min(daily_goal_progress, 100.0)  # Cap at 100%

        # Top skills in jobs
        all_job_tech_stacks = []
        for job in user.jobs:
            if job.tech_stack:
                all_job_tech_stacks.extend([s.lower() for s in job.tech_stack])
        skill_frequency = Counter(all_job_tech_stacks)
        top_skills_in_jobs = [
            {"skill": skill, "count": count}
            for skill, count in skill_frequency.most_common(5)
        ]

        # Top companies applied
        company_frequency = Counter()
        for app in (
            self.db.query(Application).filter(Application.user_id == user.id).all()
        ):
            job = self.db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                company_frequency[job.company.lower()] += 1
        top_companies_applied = [
            {"company": company, "count": count}
            for company, count in company_frequency.most_common(5)
        ]

        # Application status breakdown
        status_breakdown_query = (
            self.db.query(Application.status, func.count(Application.id))
            .filter(Application.user_id == user.id)
            .group_by(Application.status)
            .all()
        )
        application_status_breakdown = {
            status: count for status, count in status_breakdown_query
        }

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "interviews_scheduled": interviews_scheduled,
            "offers_received": offers_received,
            "rejections_received": rejections_received,
            "acceptance_rate": round(acceptance_rate, 2),
            "daily_applications_today": daily_applications_today,
            "weekly_applications": weekly_applications,
            "monthly_applications": monthly_applications,
            "daily_application_goal": daily_application_goal,
            "daily_goal_progress": round(daily_goal_progress, 2),
            "top_skills_in_jobs": top_skills_in_jobs,
            "top_companies_applied": top_companies_applied,
            "application_status_breakdown": application_status_breakdown,
        }

    def get_interview_trends(self, user: User) -> Dict[str, Any]:
        """
        Analyzes historical application data for interview patterns.
        Identifies common questions or skill areas leading to interviews.
        """
        cache_key = f"interview_trends:{user.id}"
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

        interviewed_applications = (
            self.db.query(Application)
            .filter(
                Application.user_id == user.id,
                Application.status == "interview",
                Application.interview_feedback.isnot(None),
            )
            .all()
        )

        common_questions = Counter()
        skill_areas = Counter()

        for app in interviewed_applications:
            if app.interview_feedback:
                feedback = app.interview_feedback
                if "questions" in feedback and isinstance(feedback["questions"], list):
                    for q in feedback["questions"]:
                        common_questions[q.lower()] += 1
                if "skill_areas" in feedback and isinstance(
                    feedback["skill_areas"], list
                ):
                    for s in feedback["skill_areas"]:
                        skill_areas[s.lower()] += 1

        # Get jobs associated with interviewed applications to find common tech stacks
        interviewed_job_ids = [app.job_id for app in interviewed_applications]
        interviewed_jobs = (
            self.db.query(Job).filter(Job.id.in_(interviewed_job_ids)).all()
        )

        common_tech_stack_in_interviews = Counter()
        for job in interviewed_jobs:
            if job.tech_stack:
                for skill in job.tech_stack:
                    common_tech_stack_in_interviews[skill.lower()] += 1

        result = {
            "total_interviews_analyzed": len(interviewed_applications),
            "top_common_questions": common_questions.most_common(5),
            "top_skill_areas_discussed": skill_areas.most_common(5),
            "common_tech_stack_in_interviews": common_tech_stack_in_interviews.most_common(
                5
            ),
        }

        if redis_client:
            redis_client.set(cache_key, json.dumps(result), ex=3600)

        return result
