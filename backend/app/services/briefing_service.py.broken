"""
Celery tasks for email notifications and briefings with adaptive timing
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta, time
from celery import current_app as celery_app

from ..services.email_service import email_service
from ..services.briefing_service import briefing_service
from ..models.user import User
from ..models.job import Job
from ..models.application import Application
from ..core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_morning_briefing_task(self, user_id: int):
	"""
	Send morning briefing email to a specific user with personalized content

	Args:
	    user_id: ID of the user to send briefing to
	"""
	try:
		db = next(get_db())

		# Get user information
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			logger.error(f"User {user_id} not found for morning briefing")
			return {"status": "error", "message": "User not found"}

		# Check if user wants morning briefings
		email_settings = user.settings.get("email_notifications", {})
		if not email_settings.get("morning_briefing", True):
			logger.info(f"User {user_id} has disabled morning briefings")
			return {"status": "skipped", "reason": "disabled", "user_id": user_id}

		# Generate comprehensive briefing data using briefing service
		briefing_data = briefing_service.generate_morning_briefing_data(db, user_id)

		# Send email using the briefing data
		success = email_service.send_morning_briefing(
			user_email=user.email,
			user_name=briefing_data["user_name"],
			recommendations=briefing_data["recommendations"],
			daily_goals=briefing_data["daily_goals"],
			market_insights=briefing_data["market_insights"],
			progress=briefing_data["progress"],
		)

		if success:
			logger.info(f"Morning briefing sent successfully to user {user_id}")

			# Track email sent for adaptive timing analysis
			briefing_service.update_engagement_metrics(db, user_id, "morning_briefing", "sent", datetime.now())

			return {"status": "success", "user_id": user_id}
		else:
			logger.error(f"Failed to send morning briefing to user {user_id}")
			raise Exception("Email sending failed")

	except Exception as exc:
		logger.error(f"Error sending morning briefing to user {user_id}: {exc}")
		# Retry with exponential backoff
		raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_evening_summary_task(self, user_id: int):
	"""
	Send evening summary email to a specific user with daily progress and tomorrow's plan

	Args:
	    user_id: ID of the user to send summary to
	"""
	try:
		db = next(get_db())

		# Get user information
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			logger.error(f"User {user_id} not found for evening summary")
			return {"status": "error", "message": "User not found"}

		# Check if user wants evening summaries
		email_settings = user.settings.get("email_notifications", {})
		if not email_settings.get("evening_summary", True):
			logger.info(f"User {user_id} has disabled evening summaries")
			return {"status": "skipped", "reason": "disabled", "user_id": user_id}

		# Generate comprehensive summary data using briefing service
		summary_data = briefing_service.generate_evening_summary_data(db, user_id)

		# Send email using the summary data
		success = email_service.send_evening_summary(
			user_email=user.email,
			user_name=summary_data["user_name"],
			daily_activity=summary_data["daily_activity"],
			achievements=summary_data["achievements"],
			tomorrow_plan=summary_data["tomorrow_plan"],
			motivation=summary_data["motivation"],
		)

		if success:
			logger.info(f"Evening summary sent successfully to user {user_id}")

			# Track email sent for adaptive timing analysis
			briefing_service.update_engagement_metrics(db, user_id, "evening_summary", "sent", datetime.now())

			return {"status": "success", "user_id": user_id}
		else:
			logger.error(f"Failed to send evening summary to user {user_id}")
			raise Exception("Email sending failed")

	except Exception as exc:
		logger.error(f"Error sending evening summary to user {user_id}: {exc}")
		raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_skill_gap_analysis_task(self, user_id: int):
	"""
	Send skill gap analysis email to a specific user

	Args:
	    user_id: ID of the user to send analysis to
	"""
	try:
		db = next(get_db())

		# Get user information
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			logger.error(f"User {user_id} not found for skill gap analysis")
			return {"status": "error", "message": "User not found"}

		# Generate analysis data
		skill_gaps = self._analyze_skill_gaps(db, user_id)
		learning_resources = self._get_learning_resources(skill_gaps)
		market_trends = self._get_skill_market_trends(db, user_id)

		# Send email
		success = email_service.send_skill_gap_analysis(
			user_email=user.email,
			user_name=user.profile.get("name", "there"),
			skill_gaps=skill_gaps,
			learning_resources=learning_resources,
			market_trends=market_trends,
		)

		if success:
			logger.info(f"Skill gap analysis sent successfully to user {user_id}")
			return {"status": "success", "user_id": user_id}
		else:
			logger.error(f"Failed to send skill gap analysis to user {user_id}")
			raise Exception("Email sending failed")

	except Exception as exc:
		logger.error(f"Error sending skill gap analysis to user {user_id}: {exc}")
		raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_application_milestone_task(self, user_id: int, milestone_type: str, milestone_data: Dict[str, Any]):
	"""
	Send application milestone celebration email

	Args:
	    user_id: ID of the user
	    milestone_type: Type of milestone achieved
	    milestone_data: Data specific to the milestone
	"""
	try:
		db = next(get_db())

		# Get user information
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			logger.error(f"User {user_id} not found for milestone email")
			return {"status": "error", "message": "User not found"}

		# Generate encouragement message
		encouragement = self._generate_milestone_encouragement(milestone_type, milestone_data)

		# Send email
		success = email_service.send_application_milestone(
			user_email=user.email,
			user_name=user.profile.get("name", "there"),
			milestone_type=milestone_type,
			milestone_data=milestone_data,
			encouragement=encouragement,
		)

		if success:
			logger.info(f"Milestone email sent successfully to user {user_id}")
			return {"status": "success", "user_id": user_id, "milestone": milestone_type}
		else:
			logger.error(f"Failed to send milestone email to user {user_id}")
			raise Exception("Email sending failed")

	except Exception as exc:
		logger.error(f"Error sending milestone email to user {user_id}: {exc}")
		raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task
def send_bulk_morning_briefings():
	"""
	Send morning briefings to all active users with adaptive timing
	"""
	try:
		db = next(get_db())

		# Get all active users who want morning briefings
		users = db.query(User).filter(User.settings["email_notifications"]["morning_briefing"].astext.cast(bool) == True).all()

		sent_count = 0
		failed_count = 0
		scheduled_count = 0

		current_hour = datetime.now().hour

		for user in users:
			try:
				# Get optimal timing for this user
				optimal_morning, _ = briefing_service.get_optimal_briefing_times(db, user.id)

				# If it's the user's optimal time (within 1 hour), send now
				if abs(current_hour - optimal_morning.hour) <= 1:
					send_morning_briefing_task.delay(user.id)
					sent_count += 1
				else:
					# Schedule for later at the optimal time
					schedule_personalized_morning_briefing.apply_async(
						args=[user.id], eta=datetime.now().replace(hour=optimal_morning.hour, minute=optimal_morning.minute, second=0, microsecond=0)
					)
					scheduled_count += 1

			except Exception as e:
				logger.error(f"Failed to schedule morning briefing for user {user.id}: {e}")
				failed_count += 1

		logger.info(f"Morning briefings: {sent_count} sent now, {scheduled_count} scheduled, {failed_count} failed")
		return {"status": "success", "sent_now": sent_count, "scheduled": scheduled_count, "failed": failed_count}

	except Exception as exc:
		logger.error(f"Error in bulk morning briefings: {exc}")
		return {"status": "error", "message": str(exc)}


@celery_app.task
def send_bulk_evening_summaries():
	"""
	Send evening summaries to all active users with adaptive timing
	"""
	try:
		db = next(get_db())

		# Get all active users who want evening summaries
		users = db.query(User).filter(User.settings["email_notifications"]["evening_summary"].astext.cast(bool) == True).all()

		sent_count = 0
		failed_count = 0
		scheduled_count = 0

		current_hour = datetime.now().hour

		for user in users:
			try:
				# Get optimal timing for this user
				_, optimal_evening = briefing_service.get_optimal_briefing_times(db, user.id)

				# If it's the user's optimal time (within 1 hour), send now
				if abs(current_hour - optimal_evening.hour) <= 1:
					send_evening_summary_task.delay(user.id)
					sent_count += 1
				else:
					# Schedule for later at the optimal time
					schedule_personalized_evening_summary.apply_async(
						args=[user.id], eta=datetime.now().replace(hour=optimal_evening.hour, minute=optimal_evening.minute, second=0, microsecond=0)
					)
					scheduled_count += 1

			except Exception as e:
				logger.error(f"Failed to schedule evening summary for user {user.id}: {e}")
				failed_count += 1

		logger.info(f"Evening summaries: {sent_count} sent now, {scheduled_count} scheduled, {failed_count} failed")
		return {"status": "success", "sent_now": sent_count, "scheduled": scheduled_count, "failed": failed_count}

	except Exception as exc:
		logger.error(f"Error in bulk evening summaries: {exc}")
		return {"status": "error", "message": str(exc)}


@celery_app.task(bind=True, max_retries=2)
def schedule_personalized_morning_briefing(self, user_id: int):
	"""
	Schedule morning briefing at user's optimal time

	Args:
	    user_id: ID of the user
	"""
	try:
		# This task is scheduled to run at the user's optimal time
		return send_morning_briefing_task.delay(user_id)

	except Exception as exc:
		logger.error(f"Error scheduling personalized morning briefing for user {user_id}: {exc}")
		raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@celery_app.task(bind=True, max_retries=2)
def schedule_personalized_evening_summary(self, user_id: int):
	"""
	Schedule evening summary at user's optimal time

	Args:
	    user_id: ID of the user
	"""
	try:
		# This task is scheduled to run at the user's optimal time
		return send_evening_summary_task.delay(user_id)

	except Exception as exc:
		logger.error(f"Error scheduling personalized evening summary for user {user_id}: {exc}")
		raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@celery_app.task
def adaptive_timing_analysis():
	"""
	Analyze user engagement patterns and update optimal timing recommendations
	"""
	try:
		db = next(get_db())

		# Get all active users
		users = db.query(User).all()

		updated_count = 0

		for user in users:
			try:
				# Analyze engagement patterns and update recommendations
				optimal_morning, optimal_evening = briefing_service.get_optimal_briefing_times(db, user.id)

				# Update user settings with optimal times
				if "email_notifications" not in user.settings:
					user.settings["email_notifications"] = {}

				user.settings["email_notifications"]["optimal_morning_time"] = optimal_morning.isoformat()
				user.settings["email_notifications"]["optimal_evening_time"] = optimal_evening.isoformat()

				db.commit()
				updated_count += 1

			except Exception as e:
				logger.error(f"Error updating timing for user {user.id}: {e}")
				db.rollback()
				continue

		logger.info(f"Updated optimal timing for {updated_count} users")
		return {"status": "success", "updated_users": updated_count}

	except Exception as exc:
		logger.error(f"Error in adaptive timing analysis: {exc}")
		return {"status": "error", "message": str(exc)}


@celery_app.task
def check_daily_achievements():
	"""
	Check for daily achievements and send milestone emails
	"""
	try:
		db = next(get_db())

		# Get all active users
		users = db.query(User).all()

		milestone_count = 0

		for user in users:
			try:
				# Check for achievements
				achievements = briefing_service._get_daily_achievements(db, user.id)

				# Send milestone email if significant achievements
				if len(achievements) >= 2:  # Multiple achievements
					send_application_milestone_task.delay(user.id, "daily_achievements", {"achievements": achievements, "count": len(achievements)})
					milestone_count += 1

			except Exception as e:
				logger.error(f"Error checking achievements for user {user.id}: {e}")
				continue

		logger.info(f"Sent {milestone_count} milestone emails")
		return {"status": "success", "milestones_sent": milestone_count}

	except Exception as exc:
		logger.error(f"Error checking daily achievements: {exc}")
		return {"status": "error", "message": str(exc)}


@celery_app.task
def track_email_engagement(user_id: int, email_type: str, action: str):
	"""
	Track email engagement for adaptive timing

	Args:
	    user_id: ID of the user
	    email_type: Type of email ('morning_briefing', 'evening_summary')
	    action: Action taken ('opened', 'clicked', 'applied')
	"""
	try:
		db = next(get_db())

		briefing_service.update_engagement_metrics(db, user_id, email_type, action, datetime.now())

		logger.info(f"Tracked engagement: user {user_id}, {email_type}, {action}")
		return {"status": "success", "user_id": user_id, "action": action}

	except Exception as exc:
		logger.error(f"Error tracking email engagement: {exc}")
		return {"status": "error", "message": str(exc)}


@celery_app.task
def test_email_service():
	"""
	Test email service connectivity
	"""
	try:
		success = email_service.test_connection()
		if success:
			logger.info("Email service test successful")
			return {"status": "success", "message": "Email service is working"}
		else:
			logger.error("Email service test failed")
			return {"status": "error", "message": "Email service connection failed"}
	except Exception as exc:
		logger.error(f"Email service test error: {exc}")
		return {"status": "error", "message": str(exc)}


# Helper functions for generating email content


def _get_user_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
	"""Get top job recommendations for user"""
	# This would integrate with the recommendation service
	# For now, return mock data
	return [
		{
			"id": 1,
			"title": "Senior Software Engineer",
			"company": "TechCorp",
			"location": "San Francisco, CA",
			"match_score": 0.92,
			"description": "Join our team building next-generation applications...",
			"skills": ["Python", "React", "PostgreSQL"],
			"explanation": "Strong match for your Python and React experience",
			"application_url": "https://example.com/apply/1",
		}
	]


def _generate_daily_goals(db: Session, user_id: int) -> Dict[str, Any]:
	"""Generate daily goals for user"""
	return {"applications_target": 3, "networking_target": 2, "skill_focus": "Machine Learning"}


def _get_market_insights(db: Session, user_id: int) -> Dict[str, Any]:
	"""Get market insights for user"""
	return {
		"trending_skills": ["Python", "React", "AWS", "Docker", "Kubernetes", "TypeScript", "Node.js", "PostgreSQL"],
		"salary_trend": "Software engineer salaries increased 8% this quarter in your target locations",
		"job_market_activity": "High demand for full-stack developers in your area with 15% more job postings this month",
	}


def _calculate_user_progress(db: Session, user_id: int) -> Dict[str, Any]:
	"""Calculate user's progress metrics"""
	try:
		# Get applications from last week
		week_ago = datetime.now() - timedelta(days=7)
		applications_this_week = db.query(Application).filter(Application.user_id == user_id, Application.applied_at >= week_ago).count()

		# Get interviews scheduled
		interviews_scheduled = (
			db.query(Application)
			.filter(Application.user_id == user_id, Application.status.in_(["interview_scheduled", "interview_completed"]))
			.count()
		)

		# Calculate response rate
		total_applications = db.query(Application).filter(Application.user_id == user_id).count()

		responses = db.query(Application).filter(Application.user_id == user_id, Application.response_date.isnot(None)).count()

		response_rate = (responses / total_applications * 100) if total_applications > 0 else 0

		# Calculate goal completion
		user = db.query(User).filter(User.id == user_id).first()
		weekly_goal = user.settings.get("weekly_goals", {}).get("applications", 15) if user else 15
		goal_completion = min((applications_this_week / weekly_goal * 100), 100) if weekly_goal > 0 else 0

		return {
			"applications_this_week": applications_this_week,
			"interviews_scheduled": interviews_scheduled,
			"response_rate": round(response_rate, 1),
			"goal_completion": round(goal_completion, 1),
		}

	except Exception as e:
		self.logger.error(f"Error calculating progress for user {user_id}: {e}")
		return {}


	def _get_daily_activity(db: Session, user_id: int) -> Dict[str, Any]:
	"""Get user's daily activity summary"""
	try:
		today = datetime.now().date()

		# Applications sent today
		applications_today = db.query(Application).filter(Application.user_id == user_id, func.date(Application.applied_at) == today).count()

		# Get application details for today
		applications_details = (
			db.query(Application).join(Job).filter(Application.user_id == user_id, func.date(Application.applied_at) == today).all()
		)

		formatted_applications = []
		for app in applications_details:
			formatted_applications.append(
				{"job_title": app.job.title, "company": app.job.company, "location": app.job.location, "applied_at": app.applied_at}
			)

		# Jobs viewed today (would need tracking implementation)
		jobs_viewed = 15  # Placeholder - would need view tracking

		# Profiles updated (would need tracking implementation)
		profiles_updated = 1 if applications_today > 0 else 0  # Simplified logic

		# Time spent (would need tracking implementation)
		time_spent_minutes = applications_today * 15  # Estimate 15 min per application

		# Goal achievement calculation
		user = db.query(User).filter(User.id == user_id).first()
		daily_goal = user.settings.get("daily_goals", {}).get("applications_per_day", 3) if user else 3
		goal_achievement = min((applications_today / daily_goal * 100), 100) if daily_goal > 0 else 0

		return {
			"applications_sent": applications_today,
			"applications_details": formatted_applications,
			"jobs_viewed": jobs_viewed,
			"profiles_updated": profiles_updated,
			"time_spent_minutes": time_spent_minutes,
			"goal_achievement": round(goal_achievement, 1),
			"weekly_progress": weekly_progress,
		}

	except Exception as e:
		self.logger.error(f"Error getting daily activity for user {user_id}: {e}")
		return {}


def _get_daily_achievements(db: Session, user_id: int) -> List[Dict[str, Any]]:
	"""Get user's daily achievements"""
	try:
		achievements = []
		today = datetime.now().date()

		# Check if user met application goal
		applications_today = db.query(Application).filter(Application.user_id == user_id, func.date(Application.applied_at) == today).count()

		user = db.query(User).filter(User.id == user_id).first()
		daily_goal = user.settings.get("daily_goals", {}).get("applications_per_day", 3) if user else 3

		if applications_today >= daily_goal:
			achievements.append(
				{
					"title": "Application Goal Reached",
					"description": f"You applied to {applications_today} job{'s' if applications_today != 1 else ''} today, meeting your daily goal!",
					"impact": f"Increased your weekly application count by {round(applications_today / 7 * 100, 1)}%",
				}
			)

		# Check for application streak
		streak_days = self._calculate_application_streak(db, user_id)
		if streak_days >= 3:
			achievements.append(
				{
					"title": f"{streak_days}-Day Application Streak",
					"description": f"You've applied to jobs for {streak_days} consecutive days!",
					"impact": "Consistency is key to job search success",
				}
			)

		# Check for first response/interview
		recent_responses = db.query(Application).filter(Application.user_id == user_id, func.date(Application.response_date) == today).count()

		if recent_responses > 0:
			achievements.append(
				{
					"title": "Response Received",
					"description": f"You received {recent_responses} response{'s' if recent_responses != 1 else ''} from employers today!",
					"impact": "Your applications are getting noticed",
				}
			)

		return achievements

	except Exception as e:
		self.logger.error(f"Error getting daily achievements for user {user_id}: {e}")
		return []


def _generate_tomorrow_plan(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Generate tomorrow's action plan"""
	try:
		# Get priority applications (jobs with upcoming deadlines)
		priority_applications = self._get_priority_applications(db, user_id)

		# Get follow-ups needed
		follow_ups = self._get_follow_ups_needed(db, user_id)

		# Get skill development recommendation
		skill_development = self._get_skill_development_plan(db, user_id)

		# Get networking suggestions
		networking = self._get_networking_suggestions(db, user_id)

		return {
			"priority_applications": priority_applications,
			"follow_ups": follow_ups,
			"skill_development": skill_development,
			"networking": networking,
		}

	except Exception as e:
		self.logger.error(f"Error generating tomorrow plan for user {user_id}: {e}")
		return {}


def _generate_motivational_message(self, db: Session, user_id: int) -> str:
	"""Generate personalized motivational message"""
	try:
		# Get user's recent activity to personalize message
		recent_applications = (
			db.query(Application).filter(Application.user_id == user_id, Application.applied_at >= datetime.now() - timedelta(days=7)).count()
		)

		# Get user's response rate
		total_applications = db.query(Application).filter(Application.user_id == user_id).count()

		responses = db.query(Application).filter(Application.user_id == user_id, Application.response_date.isnot(None)).count()

		# Personalized messages based on activity
		if recent_applications >= 10:
			messages = [
				"Your dedication this week has been outstanding! That level of consistency will definitely pay off.",
				"You're putting in serious work on your job search. Keep up this momentum!",
				"Your commitment to applying consistently shows real determination. Success is coming!",
			]
		elif recent_applications >= 5:
			messages = [
				"You're making steady progress on your career journey. Every application matters!",
				"Your consistent effort is building toward something great. Keep going!",
				"You're developing excellent job search habits. Stay the course!",
			]
		elif responses > 0:
			messages = [
				"Getting responses shows your qualifications are being recognized. You're on the right track!",
				"Employers are noticing you! That's proof your approach is working.",
				"Those responses are validation that you're targeting the right opportunities.",
			]
		else:
			messages = [
				"Every successful person started exactly where you are now. Your breakthrough is coming!",
				"Job searching is tough, but your persistence will make the difference.",
				"Remember: every 'no' brings you closer to the right 'yes'. Keep pushing forward!",
			]

		# Simple rotation based on user_id and day
		message_index = (user_id + datetime.now().day) % len(messages)
		return messages[message_index]

	except Exception as e:
		self.logger.error(f"Error generating motivational message for user {user_id}: {e}")
		return "Every step forward in your career journey matters. Keep up the great work!"


	def _get_weekly_progress(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Get weekly progress snapshot"""
	try:
		week_ago = datetime.now() - timedelta(days=7)

		applications = db.query(Application).filter(Application.user_id == user_id, Application.applied_at >= week_ago).count()

		responses = db.query(Application).filter(Application.user_id == user_id, Application.response_date >= week_ago).count()

		interviews = (
			db.query(Application)
			.filter(
				Application.user_id == user_id,
				Application.status.in_(["interview_scheduled", "interview_completed"]),
				Application.updated_at >= week_ago,
			)
			.count()
		)

		# Calculate streak
		streak_days = self._calculate_application_streak(db, user_id)

		return {"applications": applications, "responses": responses, "interviews": interviews, "streak_days": streak_days}

	except Exception as e:
		self.logger.error(f"Error getting weekly progress for user {user_id}: {e}")
		return {}

	# Helper methods for adaptive timing and engagement analysis


def _analyze_email_engagement(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Analyze user's email engagement patterns"""
	try:
		# Get engagement data from analytics
		engagement_data = (
			db.query(Analytics)
			.filter(Analytics.user_id == user_id, Analytics.type == "email_engagement", Analytics.generated_at >= datetime.now() - timedelta(days=30))
			.all()
		)

		if not engagement_data:
			return {}

		# Analyze patterns by hour and day of week
		hourly_engagement = {}
		daily_engagement = {}

		for entry in engagement_data:
			data = entry.data
			hour = data.get("hour", 8)
			day_of_week = data.get("day_of_week", 0)
			action = data.get("action", "opened")

			# Weight different actions
			weight = {"opened": 1, "clicked": 2, "applied": 3}.get(action, 1)

			hourly_engagement[hour] = hourly_engagement.get(hour, 0) + weight
			daily_engagement[day_of_week] = daily_engagement.get(day_of_week, 0) + weight

		return {"hourly_engagement": hourly_engagement, "daily_engagement": daily_engagement}

	except Exception as e:
		self.logger.error(f"Error analyzing email engagement for user {user_id}: {e}")
		return {}


def _analyze_activity_patterns(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Analyze user's application activity patterns"""
	try:
		# Get application data from last 30 days
		applications = (
			db.query(Application).filter(Application.user_id == user_id, Application.applied_at >= datetime.now() - timedelta(days=30)).all()
		)

		if not applications:
			return {}

		# Analyze patterns by hour and day of week
		hourly_activity = {}
		daily_activity = {}

		for app in applications:
			hour = app.applied_at.hour
			day_of_week = app.applied_at.weekday()

			hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
			daily_activity[day_of_week] = daily_activity.get(day_of_week, 0) + 1

		return {"hourly_activity": hourly_activity, "daily_activity": daily_activity}

	except Exception as e:
		self.logger.error(f"Error analyzing activity patterns for user {user_id}: {e}")
		return {}


def _calculate_optimal_morning_time(self, engagement_data: Dict, activity_patterns: Dict) -> time:
	"""Calculate optimal morning briefing time"""
	try:
		# Default to 8:00 AM
		default_hour = 8

		# If we have engagement data, use the hour with highest engagement
		if engagement_data.get("hourly_engagement"):
			# Focus on morning hours (6-11 AM)
			morning_hours = {h: v for h, v in engagement_data["hourly_engagement"].items() if 6 <= h <= 11}
			if morning_hours:
				optimal_hour = max(morning_hours, key=morning_hours.get)
				return time(optimal_hour, 0)

		# If we have activity patterns, use the most active morning hour
		if activity_patterns.get("hourly_activity"):
			morning_hours = {h: v for h, v in activity_patterns["hourly_activity"].items() if 6 <= h <= 11}
			if morning_hours:
				optimal_hour = max(morning_hours, key=morning_hours.get)
				# Send briefing 1 hour before peak activity
				briefing_hour = max(6, optimal_hour - 1)
				return time(briefing_hour, 0)

		return time(default_hour, 0)

	except Exception as e:
		self.logger.error(f"Error calculating optimal morning time: {e}")
		return time(8, 0)


def _calculate_optimal_evening_time(self, engagement_data: Dict, activity_patterns: Dict) -> time:
	"""Calculate optimal evening summary time"""
	try:
		# Default to 7:00 PM
		default_hour = 19

		# If we have engagement data, use the hour with highest evening engagement
		if engagement_data.get("hourly_engagement"):
			# Focus on evening hours (5-9 PM)
			evening_hours = {h: v for h, v in engagement_data["hourly_engagement"].items() if 17 <= h <= 21}
			if evening_hours:
				optimal_hour = max(evening_hours, key=evening_hours.get)
				return time(optimal_hour, 0)

		# If we have activity patterns, use the most active morning hour
		if activity_patterns.get("hourly_activity"):
			evening_hours = {h: v for h, v in activity_patterns["hourly_activity"].items() if 17 <= h <= 21}
			if evening_hours:
				optimal_hour = max(evening_hours, key=evening_hours.get)
				# Send briefing 1 hour before peak activity
				briefing_hour = max(17, optimal_hour - 1)
				return time(briefing_hour, 0)

		return time(default_hour, 0)

	except Exception as e:
		self.logger.error(f"Error calculating optimal evening time: {e}")
		return time(19, 0)

	# Additional helper methods (simplified implementations)


def _get_personalized_tips(self, db: Session, user_id: int) -> List[str]:
	"""Get personalized tips for the user"""
	tips = [
		"The best time to apply for jobs is between 6-10 AM when hiring managers are most active!",
		"Customize your resume for each application to increase your response rate by up to 40%.",
		"Following up on applications after 1 week shows initiative and keeps you top of mind.",
		"Networking accounts for 70% of job placements - don't underestimate its power!",
	]
	return tips[:2]  # Return 2 random tips


def _get_recent_activity_stats(self, db: Session, user_id: int, days: int = 7) -> Dict[str, Any]:
	"""Get recent activity statistics"""
	cutoff_date = datetime.now() - timedelta(days=days)
	applications = db.query(Application).filter(Application.user_id == user_id, Application.applied_at >= cutoff_date).count()

	return {"avg_applications_per_day": applications / days if days > 0 else 0}


def _get_skill_focus_recommendation(self, db: Session, user_id: int) -> str:
	"""Get skill focus recommendation"""
	# Simplified implementation
	skills = ["Python", "React", "AWS", "Docker", "Machine Learning", "Data Analysis"]
	return skills[user_id % len(skills)]


def _get_trending_skills(self, db: Session, locations: List[str]) -> List[str]:
	"""Get trending skills from job postings"""
	return ["Python", "React", "AWS", "Docker", "Kubernetes", "TypeScript", "Node.js", "PostgreSQL"]


def _get_salary_trends(self, db: Session, skills: List[str], locations: List[str]) -> str:
	"""Get salary trends for user's skill set"""
	return "Software engineer salaries increased 8% this quarter in your target locations"


def _get_market_activity(self, db: Session, locations: List[str]) -> str:
	"""Get job market activity"""
	return "High demand for full-stack developers in your area with 15% more job postings this month"


def _calculate_application_streak(self, db: Session, user_id: int) -> int:
	"""Calculate consecutive days with applications"""
	# Simplified implementation
	return 5  # Placeholder


def _get_priority_applications(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
	"""Get priority applications for tomorrow"""
	return []  # Simplified - would implement deadline tracking


def _get_follow_ups_needed(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
	"""Get follow-ups needed"""
	return []  # Simplified - would implement follow-up tracking


def _get_skill_development_plan(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Get skill development plan"""
	return {"activity": "Complete React course module", "skill": "React", "resource": "React Fundamentals on Coursera"}


def _get_networking_suggestions(self, db: Session, user_id: int) -> Dict[str, Any]:
	"""Get networking suggestions"""
	return {
		"activity": "Connect with 2 professionals on LinkedIn",
		"suggestions": ["Reach out to alumni in your target companies", "Comment on industry posts to increase visibility"],
	}


def _get_time_based_greeting(self) -> str:
	"""Get appropriate greeting based on current time"""
	hour = datetime.now().hour

	if 5 <= hour < 12:
		return "Good morning"
	elif 12 <= hour < 17:
		return "Good afternoon"
	elif 17 <= hour < 21:
		return "Good evening"
	else:
		return "Good evening"


# Global briefing service instance
briefing_service = BriefingService()
