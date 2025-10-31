"""
Consolidated Analytics Service for Career Copilot
Combines functionality from analytics.py, analytics_service.py, and analytics_data_collection_service.py
"""

import json
import logging
from collections import Counter
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.analytics import Analytics
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
	"""Analysis types for analytics operations"""

	RISK_TRENDS = "risk_trends"
	CONTRACT_COMPARISON = "contract_comparison"
	COMPLIANCE_CHECK = "compliance_check"
	COST_ANALYSIS = "cost_analysis"
	PERFORMANCE_METRICS = "performance_metrics"
	USER_ENGAGEMENT = "user_engagement"
	APPLICATION_SUCCESS = "application_success"
	MARKET_TRENDS = "market_trends"


class AnalyticsService:
	"""Consolidated analytics service handling all analytics functionality.

	This service provides methods for:
	- Collecting and processing analytics events.
	- Retrieving various metrics (user, application, market trends).
	- Generating comprehensive analytics reports.
	- Performing specialized analysis (risk, compliance, cost, performance).
	- Managing email analytics (recording events, getting metrics).
	"""

	def __init__(self, db: Session | None = None):
		"""Initializes the AnalyticsService.

		Args:
		    db: The SQLAlchemy database session.
		"""
		self.db = db
		self.logger = logging.getLogger(__name__)

	# Core Analytics Methods - Primary Interface

	def collect_event(self, event_type: str, data: dict[str, Any], user_id: int | None = None) -> bool:
		"""Collects analytics event data and stores it in the database.

		Args:
		    event_type: The type of the event (e.g., 'user_login', 'job_view').
		    data: A dictionary containing the event-specific data.
		    user_id: Optional; The ID of the user associated with the event.

		Returns:
		    True if the event was successfully collected, False otherwise.
		"""
		try:
			if not self.db:
				self.logger.warning("No database session available for event collection")
				return False

			# Create analytics record
			analytics = Analytics(
				user_id=user_id,
				type=event_type,
				data={"event_data": data, "timestamp": datetime.now(UTC).isoformat(), "event_type": event_type},
			)

			self.db.add(analytics)
			self.db.commit()
			return True

		except Exception as e:
			self.logger.error(f"Failed to collect event: {e}")
			if self.db:
				self.db.rollback()
			return False

	def process_analytics(self, batch_size: int = 100) -> dict[str, Any]:
		"""Processes a batch of unprocessed analytics data.

		Args:
			batch_size: The number of records to process in a single batch.

		Returns:
			A dictionary containing the processing results.
		"""

		try:
			if not self.db:
				return {
					"processed_count": 0,
					"batch_size": batch_size,
					"timestamp": datetime.now(UTC).isoformat(),
					"error": "No database session available",
				}

			# Get unprocessed analytics records
			unprocessed = self.db.query(Analytics).filter(Analytics.data.op("->>")("processed").is_(None)).limit(batch_size).all()

			processed_count = 0
			for record in unprocessed:
				try:
					# Mark as processed
					if isinstance(record.data, dict):
						record.data["processed"] = True
						record.data["processed_at"] = datetime.now(UTC).isoformat()
					processed_count += 1
				except Exception as e:
					self.logger.error(f"Failed to process analytics record {record.id}: {e}")

			self.db.commit()

			return {"processed_count": processed_count, "batch_size": batch_size, "timestamp": datetime.now(UTC).isoformat()}

		except Exception as e:
			self.logger.error(f"Failed to process analytics: {e}")
			if self.db:
				self.db.rollback()
			return {"processed_count": 0, "batch_size": batch_size, "timestamp": datetime.now(UTC).isoformat(), "error": str(e)}

	def get_metrics(self, metric_type: str, timeframe: str = "last_30_days", user_id: int | None = None) -> dict[str, Any]:
		"""Retrieves analytics metrics based on type, timeframe, and optional user ID.

		Args:
			metric_type: The type of metric to retrieve (e.g., 'user_activity', 'application_success_rate').
			timeframe: The period for which to retrieve metrics (e.g., 'last_7_days', 'last_30_days').
			user_id: Optional; The ID of the user for whom to retrieve metrics.

		Returns:
			A dictionary containing the requested analytics metrics.
		"""

		try:
			if not self.db:
				return {"metric_type": metric_type, "timeframe": timeframe, "user_id": user_id, "error": "No database session available"}

			# Parse timeframe
			days = self._parse_timeframe(timeframe)
			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			# Build query
			query = self.db.query(Analytics).filter(Analytics.type == metric_type, Analytics.generated_at >= cutoff_date)

			if user_id:
				query = query.filter(Analytics.user_id == user_id)

			records = query.all()

			# Aggregate metrics
			metrics = {
				"metric_type": metric_type,
				"timeframe": timeframe,
				"user_id": user_id,
				"total_records": len(records),
				"date_range": {"start": cutoff_date.isoformat(), "end": datetime.now(UTC).isoformat()},
			}

			if records:
				# Extract data from records
				data_points = [record.data for record in records if record.data]
				metrics["data_points"] = data_points
				metrics["latest_record"] = records[-1].data if records else None

			return metrics

		except Exception as e:
			self.logger.error(f"Failed to get metrics: {e}")
			return {"metric_type": metric_type, "timeframe": timeframe, "user_id": user_id, "error": str(e)}

	# User Analytics Methods (from original analytics.py)

	def get_user_analytics(self, user: User) -> dict[str, Any]:
		"""Calculates various analytics metrics for a user.

		Args:
			user: The User object for whom to calculate analytics.

		Returns:
			A dictionary containing user-specific analytics.
		"""

		if not self.db:
			return {"error": "No database session available"}

		# Basic counts
		total_jobs = self.db.query(Job).filter(Job.user_id == user.id).count()
		total_applications = self.db.query(Application).filter(Application.user_id == user.id).count()

		# Status-based counts
		pending_applications = (
			self.db.query(Application)
			.filter(
				Application.user_id == user.id,
				Application.status.in_(["interested", "applied"]),  # type: ignore[attr-defined]
			)
			.count()
		)

		interviews_scheduled = self.db.query(Application).filter(Application.user_id == user.id, Application.status == "interview").count()  # type: ignore[attr-defined]

		offers_received = (
			self.db.query(Application)
			.filter(
				Application.user_id == user.id,
				Application.status.in_(["offer", "accepted"]),  # type: ignore[attr-defined]
			)
			.count()
		)

		rejections_received = self.db.query(Application).filter(Application.user_id == user.id, Application.status == "rejected").count()  # type: ignore[attr-defined]

		# Acceptance rate
		accepted_applications = self.db.query(Application).filter(Application.user_id == user.id, Application.status == "accepted").count()  # type: ignore[attr-defined]
		acceptance_rate = (accepted_applications / offers_received * 100) if offers_received > 0 else 0.0

		# Daily, weekly, monthly applications
		today = datetime.now(UTC).date()
		daily_applications_today = self.db.query(Application).filter(Application.user_id == user.id, Application.applied_date == today).count()

		one_week_ago = today - timedelta(days=7)
		weekly_applications = self.db.query(Application).filter(Application.user_id == user.id, Application.applied_date >= one_week_ago).count()

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
		daily_application_goal = user.daily_application_goal if user.daily_application_goal is not None else 10
		daily_goal_progress = (daily_applications_today / daily_application_goal * 100) if daily_application_goal > 0 else 0.0
		daily_goal_progress = min(daily_goal_progress, 100.0)  # Cap at 100%

		# Top skills in jobs
		all_job_tech_stacks = []
		for job in user.jobs:
			if job.tech_stack:
				all_job_tech_stacks.extend([s.lower() for s in job.tech_stack])
		skill_frequency = Counter(all_job_tech_stacks)
		top_skills_in_jobs = [{"skill": skill, "count": count} for skill, count in skill_frequency.most_common(5)]

		# Top companies applied
		company_frequency: Counter[str] = Counter()
		for app in self.db.query(Application).filter(Application.user_id == user.id).all():
			job = self.db.query(Job).filter(Job.id == app.job_id).first()
			if job:
				company_frequency[job.company.lower()] += 1
		top_companies_applied = [{"company": company, "count": count} for company, count in company_frequency.most_common(5)]

		# Application status breakdown
		status_breakdown_query = (
			self.db.query(Application.status, func.count(Application.id)).filter(Application.user_id == user.id).group_by(Application.status).all()
		)
		application_status_breakdown = {status: count for status, count in status_breakdown_query}

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

	def get_interview_trends(self, user: User) -> dict[str, Any]:
		"""Analyzes historical application data for interview patterns.
		Identifies common questions or skill areas leading to interviews.

		Args:
			user: The User object for whom to analyze interview trends.

		Returns:
			A dictionary containing interview trend analytics.
		"""
		if not self.db:
			return {"error": "No database session available"}

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
				Application.interview_feedback.is_not(None),  # type: ignore[attr-defined]
			)
			.all()
		)

		common_questions: Counter[str] = Counter()
		skill_areas: Counter[str] = Counter()

		for app in interviewed_applications:
			if app.interview_feedback:
				feedback = app.interview_feedback
				if "questions" in feedback and isinstance(feedback["questions"], list):
					for q in feedback["questions"]:
						common_questions[q.lower()] += 1
				if "skill_areas" in feedback and isinstance(feedback["skill_areas"], list):
					for s in feedback["skill_areas"]:
						skill_areas[s.lower()] += 1

		# Get jobs associated with interviewed applications to find common tech stacks
		interviewed_job_ids = [app.job_id for app in interviewed_applications]
		interviewed_jobs = self.db.query(Job).filter(Job.id.in_(interviewed_job_ids)).all()

		common_tech_stack_in_interviews: Counter[str] = Counter()
		for job in interviewed_jobs:
			if job.tech_stack:
				for skill in job.tech_stack:
					common_tech_stack_in_interviews[skill.lower()] += 1

		result = {
			"total_interviews_analyzed": len(interviewed_applications),
			"top_common_questions": common_questions.most_common(5),
			"top_skill_areas_discussed": skill_areas.most_common(5),
			"common_tech_stack_in_interviews": common_tech_stack_in_interviews.most_common(5),
		}

		if redis_client:
			redis_client.set(cache_key, json.dumps(result), ex=3600)

		return result

	# User Activity Tracking Methods (from analytics_data_collection_service.py)

	def track_user_activity(self, user_id: int, activity_type: str, metadata: dict[str, Any] | None = None) -> bool:
		"""Tracks user activity for analytics purposes.

		Args:
			user_id: The ID of the user.
			activity_type: The type of activity (e.g., 'job_view', 'application_click').
			metadata: Optional; A dictionary containing additional metadata about the activity.

		Returns:
			True if the activity was successfully tracked, False otherwise.
		"""
		try:
			if not self.db:
				return False

			activity_data = {"activity_type": activity_type, "timestamp": datetime.now(UTC).isoformat(), "metadata": metadata or {}}

			# Get or create user activity analytics record for today
			today = datetime.now(UTC).date()
			existing_analytics = (
				self.db.query(Analytics)
				.filter(Analytics.user_id == user_id, Analytics.type == "user_activity", func.date(Analytics.generated_at) == today)  # type: ignore[attr-defined]
				.first()
			)

			if existing_analytics:
				# Append to existing activities
				activities = existing_analytics.data.get("activities", [])
				activities.append(activity_data)
				existing_analytics.data["activities"] = activities  # type: ignore[index]
				existing_analytics.data["activity_count"] = len(activities)  # type: ignore[index]
				existing_analytics.generated_at = datetime.now(UTC)  # type: ignore[assignment]
			else:
				# Create new analytics record
				analytics = Analytics(
					user_id=user_id, type="user_activity", data={"date": today.isoformat(), "activities": [activity_data], "activity_count": 1}
				)
				self.db.add(analytics)

			self.db.commit()
			return True

		except Exception as e:
			self.logger.error(f"Failed to track user activity: {e}")
			if self.db:
				self.db.rollback()
			return False

	def collect_user_engagement_metrics(self, user_id: int, days: int = 30) -> dict:
		"""Collects comprehensive user engagement metrics over a specified period.

		Args:
			user_id: The ID of the user.
			days: The number of days to consider for engagement metrics.

		Returns:
			A dictionary containing user engagement metrics.
		"""
		try:
			if not self.db:
				return {"error": "No database session available"}

			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			# Get user activity data
			activity_records = (
				self.db.query(Analytics)
				.filter(Analytics.user_id == user_id, Analytics.type == "user_activity", Analytics.generated_at >= cutoff_date)  # type: ignore[attr-defined]
				.all()
			)

			# Aggregate activity data
			total_activities = 0
			activity_types: dict[str, int] = {}
			daily_activities: dict[str, int] = {}

			for record in activity_records:
				activities = record.data.get("activities", [])
				total_activities += len(activities)

				for activity in activities:
					activity_type = activity.get("activity_type", "unknown")
					activity_types[activity_type] = activity_types.get(activity_type, 0) + 1

					# Track daily activity
					activity_date = activity.get("timestamp", "")[:10]  # Get date part
					daily_activities[activity_date] = daily_activities.get(activity_date, 0) + 1

			# Calculate engagement metrics
			active_days = len(daily_activities)
			avg_daily_activities = total_activities / max(active_days, 1)

			# Get job-related metrics
			jobs_viewed = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= cutoff_date).count()

			applications_submitted = (
				self.db.query(Application).filter(Application.user_id == user_id, Application.applied_date >= cutoff_date.date()).count()
			)

			return {
				"analysis_date": datetime.now(UTC).isoformat(),
				"period_days": days,
				"total_activities": total_activities,
				"active_days": active_days,
				"avg_daily_activities": round(avg_daily_activities, 2),
				"activity_breakdown": activity_types,
				"daily_activity_pattern": daily_activities,
				"jobs_viewed": jobs_viewed,
				"applications_submitted": applications_submitted,
				"engagement_score": self._calculate_engagement_score(total_activities, active_days, applications_submitted, days),
			}

		except Exception as e:
			self.logger.error(f"Failed to collect user engagement metrics: {e}")
			return {"error": f"Failed to collect engagement metrics: {e!s}"}

	def monitor_application_success_rates(self, user_id: int, days: int = 90) -> dict:
		"""Monitors and analyzes application success rates with detailed metrics.

		Args:
			user_id: The ID of the user.
			days: The number of days to consider for success rate monitoring.

		Returns:
			A dictionary containing application success rate analytics.
		"""
		try:
			if not self.db:
				return {"error": "No database session available"}

			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			# Get all applications in the period
			applications = (
				self.db.query(Application, Job).join(Job).filter(Application.user_id == user_id, Application.applied_date >= cutoff_date.date()).all()
			)

			if not applications:
				return {"error": "No applications found in the specified period"}

			# Define success stages based on APPLICATION_STATUSES
			response_statuses = ["applied", "interview", "offer", "accepted"]
			interview_statuses = ["interview", "offer", "accepted"]
			offer_statuses = ["offer", "accepted"]

			# Calculate success metrics
			total_applications = len(applications)
			responses = sum(1 for app, job in applications if app.status in response_statuses)
			interviews = sum(1 for app, job in applications if app.status in interview_statuses)
			offers = sum(1 for app, job in applications if app.status in offer_statuses)

			# Calculate rates
			response_rate = responses / total_applications if total_applications > 0 else 0
			interview_rate = interviews / total_applications if total_applications > 0 else 0
			offer_rate = offers / total_applications if total_applications > 0 else 0

			success_data = {
				"analysis_date": datetime.now(UTC).isoformat(),
				"period_days": days,
				"total_applications": total_applications,
				"success_metrics": {
					"responses_received": responses,
					"interviews_scheduled": interviews,
					"offers_received": offers,
					"response_rate": round(response_rate, 3),
					"interview_rate": round(interview_rate, 3),
					"offer_rate": round(offer_rate, 3),
					"response_percentage": f"{response_rate:.1%}",
					"interview_percentage": f"{interview_rate:.1%}",
					"offer_percentage": f"{offer_rate:.1%}",
				},
				"benchmarks": self._get_industry_benchmarks(),
				"improvement_areas": self._identify_improvement_areas(response_rate, interview_rate, offer_rate),
			}

			# Save the analysis
			self._save_analytics_data(user_id, "application_success_rate", success_data)

			return success_data

		except Exception as e:
			self.logger.error(f"Failed to monitor application success rates: {e}")
			return {"error": f"Failed to monitor success rates: {e!s}"}

	def analyze_market_trends(self, user_id: int, days: int = 90) -> dict:
		"""Analyzes job market trends from collected job data.

		Args:
			user_id: The ID of the user.
			days: The number of days to consider for market trend analysis.

		Returns:
			A dictionary containing job market trend analytics.
		"""
		try:
			if not self.db:
				return {"error": "No database session available"}

			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			# Get all jobs in the system (not just user's jobs for market analysis)
			all_jobs = self.db.query(Job).filter(Job.date_added >= cutoff_date).all()

			if not all_jobs:
				return {"error": "Insufficient job data for market analysis"}

			# Analyze job posting trends
			posting_trends = self._analyze_job_posting_trends(all_jobs)

			# Analyze salary trends
			salary_trends = self._analyze_salary_trends(all_jobs)

			# Analyze skill demand
			skill_demand = self._analyze_skill_demand(all_jobs)

			# Analyze location trends
			location_trends = self._analyze_location_trends(all_jobs)

			# Generate market insights
			market_insights = self._generate_market_insights(posting_trends, salary_trends, skill_demand, location_trends)

			market_data = {
				"analysis_date": datetime.now(UTC).isoformat(),
				"period_days": days,
				"total_jobs_analyzed": len(all_jobs),
				"posting_trends": posting_trends,
				"salary_trends": salary_trends,
				"skill_demand": skill_demand,
				"location_trends": location_trends,
				"market_insights": market_insights,
				"growth_metrics": self._calculate_market_growth_metrics(all_jobs, days),
			}

			# Save the analysis
			self._save_analytics_data(user_id, "market_trends", market_data)

			return market_data

		except Exception as e:
			self.logger.error(f"Failed to analyze market trends: {e}")
			return {"error": f"Failed to analyze market trends: {e!s}"}

	# Analysis Helper Methods (from analytics_data_collection_service.py)

	def _analyze_weekly_success_patterns(self, applications: list[tuple], response_statuses: list[str]) -> list[dict]:
		"""Analyzes success patterns by week from application data.

		Args:
			applications: A list of (Application, Job) tuples.
			response_statuses: A list of application statuses considered as a response.

		Returns:
			A list of dictionaries, each representing weekly success breakdown.
		"""
		weekly_data = {}

		for app, job in applications:
			if hasattr(app, "applied_date") and app.applied_date:
				# Convert date to datetime if needed
				if isinstance(app.applied_date, datetime):
					app_date = app.applied_date.date()
				else:
					app_date = app.applied_date

				# Get week start date (Monday)
				week_start = app_date - timedelta(days=app_date.weekday())
				week_key = week_start.isoformat()

				if week_key not in weekly_data:
					weekly_data[week_key] = {"applications": 0, "responses": 0}

				weekly_data[week_key]["applications"] += 1
				if app.status in response_statuses:
					weekly_data[week_key]["responses"] += 1

		# Convert to list and calculate rates
		weekly_breakdown = []
		for week, data in sorted(weekly_data.items()):
			success_rate = data["responses"] / data["applications"] if data["applications"] > 0 else 0
			weekly_breakdown.append(
				{
					"week_start": week,
					"applications": data["applications"],
					"responses": data["responses"],
					"success_rate": round(success_rate, 3),
					"success_percentage": f"{success_rate:.1%}",
				}
			)

		return weekly_breakdown

	def _analyze_success_by_company(self, applications: list[tuple], response_statuses: list[str]) -> dict:
		"""Analyzes application success rates by company.

		Args:
			applications: A list of (Application, Job) tuples.
			response_statuses: A list of application statuses considered as a response.

		Returns:
			A dictionary containing success rates broken down by company.
		"""
		company_data = {}

		for app, job in applications:
			company = job.company
			if company not in company_data:
				company_data[company] = {"applications": 0, "responses": 0}

			company_data[company]["applications"] += 1
			if app.status in response_statuses:
				company_data[company]["responses"] += 1

		# Calculate success rates and sort
		company_analysis = {}
		for company, data in company_data.items():
			if data["applications"] >= 2:  # Only include companies with multiple applications
				success_rate = float(data["responses"]) / float(data["applications"])
				company_analysis[company] = {
					"applications": data["applications"],
					"responses": data["responses"],
					"success_rate": round(success_rate, 3),
					"success_percentage": f"{success_rate:.1%}",
				}

		return dict(sorted(company_analysis.items(), key=lambda x: float(x[1]["success_rate"]), reverse=True))  # type: ignore[arg-type,return-value]

	def _analyze_success_by_source(self, applications: list[tuple], response_statuses: list[str]) -> dict:
		"""Analyzes application success rates by job source.

		Args:
			applications: A list of (Application, Job) tuples.
			response_statuses: A list of application statuses considered as a response.

		Returns:
			A dictionary containing success rates broken down by job source.
		"""
		source_data = {}

		for app, job in applications:
			source = getattr(job, "source", "Unknown")
			if source not in source_data:
				source_data[source] = {"applications": 0, "responses": 0}

			source_data[source]["applications"] += 1
			if app.status in response_statuses:
				source_data[source]["responses"] += 1

		# Calculate success rates
		source_analysis = {}
		for source, data in source_data.items():
			success_rate = data["responses"] / data["applications"] if data["applications"] > 0 else 0
			source_analysis[source] = {
				"applications": data["applications"],
				"responses": data["responses"],
				"success_rate": round(success_rate, 3),
				"success_percentage": f"{success_rate:.1%}",
			}

		return dict(sorted(source_analysis.items(), key=lambda x: float(x[1]["success_rate"]), reverse=True))  # type: ignore[arg-type,return-value]

	def _categorize_skill_demand(self, percentage: float) -> str:
		"""Categorizes a skill's demand level based on its percentage in job requirements.

		Args:
			percentage: The percentage of jobs requiring the skill.

		Returns:
			A string representing the demand level ('very_high', 'high', 'moderate', 'low', 'very_low').
		"""
		if percentage >= 50:
			return "very_high"
		elif percentage >= 30:
			return "high"
		elif percentage >= 15:
			return "moderate"
		elif percentage >= 5:
			return "low"
		else:
			return "very_low"

	def _categorize_skills(self, skills: dict) -> dict:
		"""Categorizes skills into predefined groups (e.g., programming languages, frameworks).

		Args:
			skills: A dictionary of skills with their demand data.

		Returns:
			A dictionary with skills categorized by type.
		"""
		categories = {
			"programming_languages": [],
			"frameworks": [],
			"databases": [],
			"cloud_platforms": [],
			"tools": [],
			"soft_skills": [],
			"other": [],
		}

		# Define skill categories (simplified mapping)
		programming_languages = ["python", "javascript", "java", "c++", "c#", "go", "rust", "typescript", "php", "ruby"]
		frameworks = ["react", "angular", "vue", "django", "flask", "spring", "express", "fastapi", "laravel"]
		databases = ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "oracle"]
		cloud_platforms = ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"]
		tools = ["git", "jenkins", "jira", "confluence", "slack", "figma", "postman"]
		soft_skills = ["communication", "leadership", "teamwork", "problem-solving", "analytical"]

		for skill, data in skills.items():
			skill_lower = skill.lower()
			if any(lang in skill_lower for lang in programming_languages):
				categories["programming_languages"].append({skill: data})
			elif any(fw in skill_lower for fw in frameworks):
				categories["frameworks"].append({skill: data})
			elif any(db in skill_lower for db in databases):
				categories["databases"].append({skill: data})
			elif any(cloud in skill_lower for cloud in cloud_platforms):
				categories["cloud_platforms"].append({skill: data})
			elif any(tool in skill_lower for tool in tools):
				categories["tools"].append({skill: data})
			elif any(soft in skill_lower for soft in soft_skills):
				categories["soft_skills"].append({skill: data})
			else:
				categories["other"].append({skill: data})

		return categories

	def _identify_emerging_skills(self, skill_demand: dict) -> list[dict]:
		"""Identifies emerging skills based on their demand level.

		Args:
			skill_demand: A dictionary of skills with their demand data.

		Returns:
			A list of dictionaries, each representing an emerging skill.
		"""
		# This is a simplified implementation - in practice, you'd compare with historical data
		emerging = []
		for skill, data in skill_demand.items():
			if data["demand_level"] in ["moderate", "low"] and data["count"] >= 3:
				emerging.append(
					{
						"skill": skill,
						"count": data["count"],
						"percentage": data["percentage"],
						"growth_potential": "high" if data["percentage"] > 10 else "moderate",
					}
				)

		return sorted(emerging, key=lambda x: x["percentage"], reverse=True)[:10]

	def _analyze_company_trends(self, jobs: list[Job]) -> dict:
		"""Analyzes company hiring trends from job data.

		Args:
			jobs: A list of Job objects.

		Returns:
			A dictionary containing company hiring trend analytics.
		"""
		company_counts: dict[str, int] = {}

		for job in jobs:
			company = job.company
			company_counts[company] = company_counts.get(company, 0) + 1

		# Calculate statistics
		job_counts = list(company_counts.values())
		avg_jobs_per_company = sum(job_counts) / len(job_counts) if job_counts else 0

		# Identify top hiring companies
		top_companies = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10])

		# Categorize companies by hiring volume
		hiring_categories = {
			"high_volume": len([c for c in job_counts if c >= 5]),
			"medium_volume": len([c for c in job_counts if 2 <= c < 5]),
			"low_volume": len([c for c in job_counts if c == 1]),
		}

		return {
			"total_companies": len(company_counts),
			"avg_jobs_per_company": round(avg_jobs_per_company, 1),
			"top_hiring_companies": top_companies,
			"hiring_volume_distribution": hiring_categories,
		}

	# Utility Methods

	def _parse_timeframe(self, timeframe: str) -> int:
		"""Parse timeframe string to days"""
		if timeframe == "last_7_days":
			return 7
		elif timeframe == "last_30_days":
			return 30
		elif timeframe == "last_90_days":
			return 90
		elif timeframe.endswith("d"):
			return int(timeframe[:-1])
		else:
			return 30  # Default to 30 days

	def _calculate_engagement_score(self, total_activities: int, active_days: int, applications: int, period_days: int) -> float:
		"""Calculate user engagement score (0-100)"""
		# Normalize metrics
		activity_score = min(total_activities / (period_days * 5), 1.0) * 40  # Max 40 points
		consistency_score = (active_days / period_days) * 30  # Max 30 points
		application_score = min(applications / (period_days / 7), 1.0) * 30  # Max 30 points

		return round(activity_score + consistency_score + application_score, 2)

	def _get_industry_benchmarks(self) -> dict:
		"""Get industry benchmark success rates"""
		return {
			"response_rate": {"low": 0.15, "average": 0.25, "high": 0.40},
			"interview_rate": {"low": 0.05, "average": 0.10, "high": 0.20},
			"offer_rate": {"low": 0.01, "average": 0.03, "high": 0.08},
		}

	def _identify_improvement_areas(self, response_rate: float, interview_rate: float, offer_rate: float) -> list[str]:
		"""Identify areas for improvement based on success rates"""
		improvements = []
		benchmarks = self._get_industry_benchmarks()

		if response_rate < benchmarks["response_rate"]["low"]:
			improvements.append("Low response rate - improve resume and application targeting")

		if interview_rate < benchmarks["interview_rate"]["low"]:
			improvements.append("Low interview rate - enhance application quality and job matching")

		if offer_rate < benchmarks["offer_rate"]["low"]:
			improvements.append("Low offer rate - focus on interview preparation and skills development")

		return improvements

	def _analyze_job_posting_trends(self, jobs: list[Job]) -> dict:
		"""Analyze job posting volume trends over time"""
		daily_counts: dict[str, int] = {}

		for job in jobs:
			if job.date_added:
				date_key = job.date_added.date().isoformat()
				daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

		return {
			"daily_posting_counts": daily_counts,
			"peak_posting_day": max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None,
			"avg_daily_postings": round(sum(daily_counts.values()) / len(daily_counts), 1) if daily_counts else 0,
		}

	def _analyze_salary_trends(self, jobs: list[Job]) -> dict:
		"""Analyze salary trends across job postings"""
		salary_data = []

		for job in jobs:
			if job.salary_min and job.salary_max:
				avg_salary = (job.salary_min + job.salary_max) / 2
				salary_data.append(avg_salary)

		if not salary_data:
			return {"error": "No salary data available"}

		salary_data.sort()  # type: ignore[arg-type]
		n = len(salary_data)
		median_salary = salary_data[n // 2] if n % 2 == 1 else (salary_data[n // 2 - 1] + salary_data[n // 2]) / 2

		return {
			"total_jobs_with_salary": len(salary_data),
			"overall_statistics": {
				"average": round(sum(salary_data) / len(salary_data), 0),
				"median": round(median_salary, 0),
				"min": min(salary_data),
				"max": max(salary_data),
			},
		}

	def _analyze_skill_demand(self, jobs: list[Job]) -> dict:
		"""Analyze skill demand from job requirements"""
		skill_counts: dict[str, int] = {}
		total_jobs_with_skills = 0

		for job in jobs:
			if job.requirements and isinstance(job.requirements, dict):
				skills = job.requirements.get("skills_required", [])
				if skills:
					total_jobs_with_skills += 1
					for skill in skills:
						if isinstance(skill, str):
							skill_lower = skill.lower().strip()
							skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1

		if not skill_counts:
			return {"error": "No skill data available in job requirements"}

		# Calculate skill demand percentages
		skill_demand = {}
		for skill, count in skill_counts.items():
			percentage = (count / total_jobs_with_skills) * 100
			skill_demand[skill] = {"count": count, "percentage": round(percentage, 1)}

		# Sort by demand
		top_skills = dict(sorted(skill_demand.items(), key=lambda x: x[1]["count"], reverse=True)[:20])

		return {"total_jobs_analyzed": total_jobs_with_skills, "unique_skills_found": len(skill_counts), "top_skills": top_skills}

	def _analyze_location_trends(self, jobs: list[Job]) -> dict:
		"""Analyze job location trends"""
		location_counts: dict[str, int] = {}
		remote_count = 0

		for job in jobs:
			location = job.location or "Unknown"

			# Check for remote work indicators
			if any(term in location.lower() for term in ["remote", "anywhere", "work from home"]):
				remote_count += 1
				location = "Remote"

			location_counts[location] = location_counts.get(location, 0) + 1

		# Calculate percentages
		total_jobs = len(jobs)
		location_analysis = {}
		for location, count in location_counts.items():
			percentage = (count / total_jobs) * 100
			location_analysis[location] = {"count": count, "percentage": round(percentage, 1)}

		# Sort by count
		top_locations = dict(sorted(location_analysis.items(), key=lambda x: x[1]["count"], reverse=True)[:15])

		return {
			"total_jobs": total_jobs,
			"remote_jobs": remote_count,
			"remote_percentage": round((remote_count / total_jobs) * 100, 1),
			"top_locations": top_locations,
		}

	def _generate_market_insights(self, posting_trends: dict, salary_trends: dict, skill_demand: dict, location_trends: dict) -> list[str]:
		"""Generates market insights from various trend analyses.

		Args:
			posting_trends: Dictionary of job posting trends.
			salary_trends: Dictionary of salary trends.
			skill_demand: Dictionary of skill demand analysis.
			location_trends: Dictionary of job location trends.

		Returns:
			A list of strings, each representing a market insight.
		"""
		insights = []

		# Posting trends insights
		if "avg_daily_postings" in posting_trends:
			insights.append(f"Average daily job postings: {posting_trends['avg_daily_postings']}")

		# Salary trends insights
		if "overall_statistics" in salary_trends:
			avg_salary = salary_trends["overall_statistics"]["average"]
			insights.append(f"Average salary across all positions: ${avg_salary:,.0f}")

		# Skill demand insights
		if "top_skills" in skill_demand:
			top_skill = list(skill_demand["top_skills"].keys())[0]
			top_skill_pct = skill_demand["top_skills"][top_skill]["percentage"]
			insights.append(f"Most in-demand skill: {top_skill.title()} ({top_skill_pct}% of jobs)")

		# Location insights
		if "remote_percentage" in location_trends:
			remote_pct = location_trends["remote_percentage"]
			insights.append(f"Remote work opportunities: {remote_pct}% of all jobs")

		return insights

	def _calculate_market_growth_metrics(self, jobs: list[Job], days: int) -> dict:
		"""Calculates market growth metrics based on job data over time.

		Args:
			jobs: A list of Job objects.
			days: The number of days to consider for growth calculation.

		Returns:
			A dictionary containing market growth metrics.
		"""
		if days < 14:
			return {"error": "Insufficient time period for growth calculation"}

		# Split period in half to compare growth
		mid_point = datetime.now(UTC) - timedelta(days=days // 2)

		recent_jobs = [job for job in jobs if job.date_added and job.date_added >= mid_point]
		earlier_jobs = [job for job in jobs if job.date_added and job.date_added < mid_point]

		recent_count = len(recent_jobs)
		earlier_count = len(earlier_jobs)

		# Calculate growth rate
		if earlier_count > 0:
			growth_rate = ((recent_count - earlier_count) / earlier_count) * 100
		else:
			growth_rate = 0

		return {
			"recent_period_jobs": recent_count,
			"earlier_period_jobs": earlier_count,
			"growth_rate_percentage": round(growth_rate, 1),
			"growth_trend": "increasing" if growth_rate > 5 else "decreasing" if growth_rate < -5 else "stable",
		}

	def _save_analytics_data(self, user_id: int, analytics_type: str, data: dict) -> bool:
		"""Save analytics data to database"""
		try:
			if not self.db:
				return False

			analytics = Analytics(user_id=user_id, type=analytics_type, data=data)
			self.db.add(analytics)
			self.db.commit()
			return True
		except Exception as e:
			self.logger.error(f"Failed to save analytics data: {e}")
			if self.db:
				self.db.rollback()
			return False

	def batch_collect_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:
		"""Collects multiple analytics events in a single batch.

		Args:
			events: A list of event dictionaries, each containing 'event_type', 'data', and optional 'user_id'.

		Returns:
			A dictionary with collection statistics (successful, failed, total events).
		"""
		successful = 0
		failed = 0

		try:
			if not self.db:
				return {"successful": 0, "failed": len(events), "error": "No database session available"}

			for event in events:
				try:
					result = self.collect_event(
						event_type=event.get("event_type", "unknown"), data=event.get("data", {}), user_id=event.get("user_id")
					)
					if result:
						successful += 1
					else:
						failed += 1
				except Exception as e:
					self.logger.error(f"Failed to collect event in batch: {e}")
					failed += 1

			return {"successful": successful, "failed": failed, "total": len(events), "timestamp": datetime.now(UTC).isoformat()}

		except Exception as e:
			self.logger.error(f"Batch event collection failed: {e}")
			return {"successful": successful, "failed": failed + (len(events) - successful - failed), "total": len(events), "error": str(e)}

	def get_comprehensive_analytics_report(self, user_id: int, days: int = 90) -> dict:
		"""Generate comprehensive analytics report combining all data collection methods"""
		try:
			if not self.db:
				return {"error": "No database session available"}

			# Get user object
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				return {"error": "User not found"}

			# Collect all analytics data
			user_analytics = self.get_user_analytics(user)
			interview_trends = self.get_interview_trends(user)
			user_engagement = self.collect_user_engagement_metrics(user_id, days)
			application_success = self.monitor_application_success_rates(user_id, days)
			market_trends = self.analyze_market_trends(user_id, days)

			# Generate overall insights
			overall_insights = []

			if "error" not in user_engagement:
				engagement_score = user_engagement.get("engagement_score", 0)
				overall_insights.append(f"User engagement score: {engagement_score}/100")

			if "error" not in application_success:
				response_rate = application_success.get("success_metrics", {}).get("response_percentage", "0%")
				overall_insights.append(f"Application response rate: {response_rate}")

			if "error" not in market_trends:
				total_jobs = market_trends.get("total_jobs_analyzed", 0)
				overall_insights.append(f"Market analysis based on {total_jobs} job postings")

			comprehensive_report = {
				"generated_at": datetime.now(UTC).isoformat(),
				"analysis_period_days": days,
				"user_id": user_id,
				"user_analytics": user_analytics,
				"interview_trends": interview_trends,
				"user_engagement_metrics": user_engagement,
				"application_success_monitoring": application_success,
				"market_trend_analysis": market_trends,
				"overall_insights": overall_insights,
				"report_summary": {
					"engagement_healthy": user_engagement.get("engagement_score", 0) > 50 if "error" not in user_engagement else False,
					"application_performance": "good"
					if application_success.get("success_metrics", {}).get("response_rate", 0) > 0.2
					else "needs_improvement"
					if "error" not in application_success
					else "unknown",
					"market_activity": "active"
					if market_trends.get("total_jobs_analyzed", 0) > 100
					else "moderate"
					if "error" not in market_trends
					else "unknown",
				},
			}

			# Save comprehensive report
			self._save_analytics_data(user_id, "comprehensive_analytics_report", comprehensive_report)

			return comprehensive_report

		except Exception as e:
			self.logger.error(f"Failed to generate comprehensive analytics report: {e}")
			return {"error": f"Failed to generate comprehensive report: {e!s}", "generated_at": datetime.now(UTC).isoformat()}

		# Advanced Analytics Methods (for API compatibility)

	async def analyze_risk_trends(self, time_period: str = "30d", contract_types: list[str] | None = None, user_id: str | None = None) -> dict[str, Any]:
		"""Analyzes risk trends over time (placeholder implementation).

		Args:
			time_period: The period for which to analyze risk trends (e.g., '30d', '90d').
			contract_types: Optional; A list of contract types to filter the analysis.
			user_id: Optional; The ID of the user for whom to analyze risk trends.

		Returns:
			A dictionary containing risk trend analysis results.
		"""
		try:
			# Parse time period
			days = self._parse_timeframe(time_period)

			# This is a placeholder implementation for risk trend analysis
			# In a real implementation, this would analyze contract risks, compliance issues, etc.
			return {
				"period": time_period,
				"average_risk_score": 2.5,  # Scale of 1-5
				"risk_count": 15,
				"high_risk_percentage": 20.0,
				"trend": "stable",
				"confidence": 0.85,
				"metadata": {
					"analysis_date": datetime.now(UTC).isoformat(),
					"contract_types_analyzed": contract_types or ["all"],
					"user_filter": user_id,
				},
			}
		except Exception as e:
			self.logger.error(f"Risk trend analysis failed: {e}")
			return {"error": f"Risk trend analysis failed: {e!s}"}

	async def compare_contracts(self, contract_1_id: str, contract_2_id: str, comparison_type: str = "comprehensive") -> dict:
		"""Compares two contracts for similarities and differences (placeholder implementation).

		Args:
			contract_1_id: The ID of the first contract.
			contract_2_id: The ID of the second contract.
			comparison_type: The type of comparison to perform (e.g., 'comprehensive', 'risk_only').

		Returns:
			A dictionary containing the contract comparison results.
		"""
		try:
			# This is a placeholder implementation for contract comparison
			# In a real implementation, this would analyze contract content, terms, risks, etc.
			return {
				"contract_1_id": contract_1_id,
				"contract_2_id": contract_2_id,
				"similarity_score": 0.75,
				"risk_differences": [
					{"type": "liability", "severity": "medium", "description": "Different liability clauses"},
					{"type": "termination", "severity": "low", "description": "Varying termination notice periods"},
				],
				"clause_differences": [
					{"section": "payment_terms", "difference": "Net 30 vs Net 45 payment terms"},
					{"section": "intellectual_property", "difference": "Different IP ownership clauses"},
				],
				"recommendations": ["Review liability clauses for consistency", "Standardize payment terms across contracts"],
			}
		except Exception as e:
			self.logger.error(f"Contract comparison failed: {e}")
			return {"error": f"Contract comparison failed: {e!s}"}

	async def check_compliance(self, contract_id: str, regulatory_framework: str = "general") -> dict:
		"""Checks contract compliance with a specified regulatory framework (placeholder implementation).

		Args:
			contract_id: The ID of the contract to check.
			regulatory_framework: The regulatory framework to check against (e.g., 'GDPR', 'HIPAA').

		Returns:
			A dictionary containing the compliance check results.
		"""
		try:
			# This is a placeholder implementation for compliance checking
			# In a real implementation, this would check against specific regulatory requirements
			return {
				"contract_id": contract_id,
				"compliance_score": 0.88,
				"violations": [
					{"type": "data_privacy", "severity": "medium", "description": "Missing GDPR compliance clause"},
					{"type": "accessibility", "severity": "low", "description": "No ADA compliance statement"},
				],
				"recommendations": ["Add GDPR compliance clause to data handling section", "Include accessibility compliance statement"],
				"regulatory_framework": regulatory_framework,
			}
		except Exception as e:
			self.logger.error(f"Compliance check failed: {e}")
			return {"error": f"Compliance check failed: {e!s}"}

	async def analyze_costs(self, time_period: str = "30d", breakdown_by: str = "model") -> dict:
		"""Analyzes AI operation costs over a specified period.

		Args:
			time_period: The period for which to analyze costs (e.g., '30d', '90d').
			breakdown_by: The category by which to break down the costs (e.g., 'model', 'user').

		Returns:
			A dictionary containing AI operation cost analysis results.
		"""
		try:
			# Parse time period
			days = self._parse_timeframe(time_period)
			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			if not self.db:
				return {"error": "No database session available"}

			# Get analytics records for cost analysis
			cost_records = (
				self.db.query(Analytics)
				.filter(Analytics.type.in_(["ai_operation", "llm_usage", "api_call"]), Analytics.generated_at >= cutoff_date)  # type: ignore[attr-defined]
				.all()
			)

			total_cost = 0.0
			breakdown: dict[str, float] = {}

			for record in cost_records:
				# Extract cost data from analytics records
				cost_data = record.data.get("cost", 0.0) if record.data else 0.0
				total_cost += cost_data

				# Breakdown by specified category
				if breakdown_by == "model":
					model = record.data.get("model", "unknown") if record.data else "unknown"
					breakdown[model] = breakdown.get(model, 0.0) + cost_data
				elif breakdown_by == "user":
					user_id = str(record.user_id) if record.user_id else "anonymous"
					breakdown[user_id] = breakdown.get(user_id, 0.0) + cost_data
				elif breakdown_by == "analysis_type":
					analysis_type = record.type
					breakdown[analysis_type] = breakdown.get(analysis_type, 0.0) + cost_data

			return {
				"time_period": time_period,
				"total_cost": round(total_cost, 2),
				"breakdown_by": breakdown_by,
				"breakdown": breakdown,
				"analysis_date": datetime.now(UTC).isoformat(),
				"records_analyzed": len(cost_records),
			}

		except Exception as e:
			self.logger.error(f"Cost analysis failed: {e}")
			return {"error": f"Cost analysis failed: {e!s}"}

	async def get_performance_metrics(self, time_period: str = "7d") -> dict:
		"""Retrieves system performance metrics over a specified period.

		Args:
			time_period: The period for which to retrieve performance metrics (e.g., '7d', '30d').

		Returns:
			A dictionary containing system performance metrics.
		"""
		try:
			# Parse time period
			days = self._parse_timeframe(time_period)
			cutoff_date = datetime.now(UTC) - timedelta(days=days)

			if not self.db:
				return {"error": "No database session available"}

			# Get performance-related analytics records
			performance_records = (
				self.db.query(Analytics)
				.filter(Analytics.type.in_(["performance", "system_metrics", "response_time"]), Analytics.generated_at >= cutoff_date)  # type: ignore[attr-defined]
				.all()
			)

			# Calculate performance metrics
			response_times = []
			error_count = 0
			success_count = 0

			for record in performance_records:
				if record.data:
					response_time = record.data.get("response_time")
					if response_time:
						response_times.append(response_time)

					status = record.data.get("status", "success")
					if status == "error":
						error_count += 1
					else:
						success_count += 1

			# Calculate averages
			avg_response_time = sum(response_times) / len(response_times) if response_times else 0
			total_requests = success_count + error_count
			error_rate = (error_count / total_requests) if total_requests > 0 else 0

			return {
				"time_period": time_period,
				"analysis_date": datetime.now(UTC).isoformat(),
				"total_requests": total_requests,
				"successful_requests": success_count,
				"failed_requests": error_count,
				"error_rate": round(error_rate, 3),
				"error_percentage": f"{error_rate:.1%}",
				"average_response_time": round(avg_response_time, 3),
				"response_time_unit": "seconds",
				"records_analyzed": len(performance_records),
			}

		except Exception as e:
			self.logger.error(f"Performance metrics retrieval failed: {e}")
			return {"error": f"Performance metrics retrieval failed: {e!s}"}


# Global service instance and factory function
def get_analytics_service(db: Session | None = None) -> AnalyticsService:
	"""Get the analytics service instance."""
	if db is None:
		db = next(get_db())
	return AnalyticsService(db=db)


# Global service instance for backward compatibility
analytics_service = AnalyticsService()
analytics_data_collection_service = AnalyticsService()
