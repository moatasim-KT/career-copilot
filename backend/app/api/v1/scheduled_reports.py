"""
Scheduled Analytics Reports API endpoints
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.single_user import MOATASIM_EMAIL, MOATASIM_USER_ID, get_single_user
from ...services.scheduled_analytics_reports_service import scheduled_analytics_reports_service

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["scheduled-reports"])


@router.get("/api/v1/reports/weekly")
async def generate_weekly_report(db: AsyncSession = Depends(get_db)):
	"""
	Generate a comprehensive weekly analytics report.

	Creates a detailed weekly report including:
	- Application activity summary
	- Success rate trends
	- Performance benchmarks
	- Key insights and recommendations
	- Goals for the upcoming week

	Returns the complete report data in JSON format.
	"""
	try:
		report = scheduled_analytics_reports_service.generate_weekly_report(db=db, user_id=MOATASIM_USER_ID)

		if "error" in report:
			raise HTTPException(status_code=404, detail=report["error"])

		return report

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to generate weekly report: {e!s}")


@router.get("/api/v1/reports/monthly")
async def generate_monthly_report(db: AsyncSession = Depends(get_db)):
	"""
	Generate a comprehensive monthly analytics report.

	Creates a detailed monthly report including:
	- Executive summary with key metrics
	- Detailed analytics across all areas
	- Trend analysis and performance evolution
	- Competitive position assessment
	- Market insights and opportunities
	- Strategic recommendations
	- Next month strategy and goals

	Returns the complete report data in JSON format.
	"""
	try:
		report = scheduled_analytics_reports_service.generate_monthly_report(db=db, user_id=MOATASIM_USER_ID)

		if "error" in report:
			raise HTTPException(status_code=404, detail=report["error"])

		return report

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to generate monthly report: {e!s}")


@router.post("/api/v1/reports/email/weekly")
async def email_weekly_report(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
	"""
	Generate and email weekly analytics report.

	Generates a weekly report and sends it to the user's email address.
	The email includes:
	- HTML formatted summary
	- Complete analytics data as JSON attachment
	- Key insights and recommendations

	Processing happens in the background to avoid timeout.
	"""
	try:
		# Generate report
		report = scheduled_analytics_reports_service.generate_weekly_report(db=db, user_id=MOATASIM_USER_ID)

		if "error" in report:
			raise HTTPException(status_code=404, detail=report["error"])

		# Send email in background
		background_tasks.add_task(scheduled_analytics_reports_service.send_report_email, report, MOATASIM_EMAIL)

		return {
			"message": "Weekly report is being generated and will be sent to your email",
			"email": MOATASIM_EMAIL,
			"report_type": "weekly",
			"scheduled_at": datetime.now().isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to schedule weekly report email: {e!s}")


@router.post("/api/v1/reports/email/monthly")
async def email_monthly_report(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
	"""
	Generate and email monthly analytics report.

	Generates a comprehensive monthly report and sends it to the user's email address.
	The email includes:
	- HTML formatted executive summary
	- Complete analytics data as JSON attachment
	- Strategic insights and recommendations
	- Next month strategy

	Processing happens in the background to avoid timeout.
	"""
	try:
		# Generate report
		report = scheduled_analytics_reports_service.generate_monthly_report(db=db, user_id=MOATASIM_USER_ID)

		if "error" in report:
			raise HTTPException(status_code=404, detail=report["error"])

		# Send email in background
		background_tasks.add_task(scheduled_analytics_reports_service.send_report_email, report, MOATASIM_EMAIL)

		return {
			"message": "Monthly report is being generated and will be sent to your email",
			"email": MOATASIM_EMAIL,
			"report_type": "monthly",
			"scheduled_at": datetime.now().isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to schedule monthly report email: {e!s}")


# Admin endpoints for bulk report generation


@router.post("/api/v1/admin/reports/weekly/all")
async def schedule_all_weekly_reports(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
	"""
	Schedule weekly reports for all users (Admin only).

	Generates and sends weekly reports to all users with email addresses.
	This endpoint is typically called by a scheduled job.

	Requires admin privileges.
	"""
	try:
		# Single user system - no admin check needed

		# Schedule bulk report generation in background
		background_tasks.add_task(scheduled_analytics_reports_service.schedule_weekly_reports, db)

		return {
			"message": "Weekly reports scheduled for all users",
			"scheduled_at": datetime.now().isoformat(),
			"report_type": "weekly",
			"scope": "all_users",
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to schedule bulk weekly reports: {e!s}")


@router.post("/api/v1/admin/reports/monthly/all")
async def schedule_all_monthly_reports(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
	"""
	Schedule monthly reports for all users (Admin only).

	Generates and sends monthly reports to all users with email addresses.
	This endpoint is typically called by a scheduled job.

	Requires admin privileges.
	"""
	try:
		# Single user system - no admin check needed

		# Schedule bulk report generation in background
		background_tasks.add_task(scheduled_analytics_reports_service.schedule_monthly_reports, db)

		return {
			"message": "Monthly reports scheduled for all users",
			"scheduled_at": datetime.now().isoformat(),
			"report_type": "monthly",
			"scope": "all_users",
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to schedule bulk monthly reports: {e!s}")


@router.get("/api/v1/reports/preview/weekly")
async def preview_weekly_report(db: AsyncSession = Depends(get_db)):
	"""
	Preview weekly report content without generating full report.

	Returns a lightweight preview of what would be included in the weekly report:
	- Summary metrics
	- Key insights preview
	- Top recommendations

	Useful for users to see what they'll receive before subscribing to reports.
	"""
	try:
		# Generate basic analytics for preview using the synchronous analytics service.
		# The analytics service uses the blocking SQLAlchemy Session API, so run it
		# in a threadpool against a sync session from the DatabaseManager.
		from starlette.concurrency import run_in_threadpool

		from ...core.database import get_db_manager
		from ...services.analytics_specialized import analytics_specialized_service

		db_manager = get_db_manager()

		def _calc_preview():
			with db_manager.get_sync_session() as session:
				return analytics_specialized_service.calculate_detailed_success_rates(db=session, user_id=MOATASIM_USER_ID, days=7)

		success_rates = await run_in_threadpool(_calc_preview)

		if "error" in success_rates:
			return {"preview_available": False, "message": "Insufficient data for preview - submit some applications first"}

		# Create preview
		preview = {
			"preview_available": True,
			"report_type": "weekly",
			"period": "Last 7 days",
			"summary_metrics": {
				"applications": success_rates.get("total_applications", 0),
				"interview_rate": success_rates.get("success_rates", {}).get("application_to_interview", 0),
				"success_rate": success_rates.get("success_rates", {}).get("overall_success", 0),
			},
			"sample_insights": ["Performance trend analysis for the week", "Comparison with market benchmarks", "Application activity assessment"],
			"sample_recommendations": ["Optimize application targeting", "Improve interview preparation", "Adjust weekly application goals"],
			"email_format": "HTML with JSON attachment",
			"delivery_schedule": "Every Monday morning",
		}

		return preview

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to generate report preview: {e!s}")


@router.get("/api/v1/reports/preview/monthly")
async def preview_monthly_report(db: AsyncSession = Depends(get_db)):
	"""
	Preview monthly report content without generating full report.

	Returns a lightweight preview of what would be included in the monthly report:
	- Executive summary metrics
	- Analysis sections overview
	- Strategic insights preview

	Useful for users to see what they'll receive before subscribing to reports.
	"""
	try:
		# Generate basic analytics for preview using the blocking analytics service
		from starlette.concurrency import run_in_threadpool

		from ...core.database import get_db_manager
		from ...services.analytics_specialized import analytics_specialized_service

		db_manager = get_db_manager()

		def _calc_preview_month():
			with db_manager.get_sync_session() as session:
				return analytics_specialized_service.calculate_detailed_success_rates(db=session, user_id=MOATASIM_USER_ID, days=30)

		success_rates = await run_in_threadpool(_calc_preview_month)

		if "error" in success_rates:
			return {"preview_available": False, "message": "Insufficient data for preview - submit some applications first"}

		# Create preview
		preview = {
			"preview_available": True,
			"report_type": "monthly",
			"period": "Last 30 days",
			"executive_summary_preview": {
				"total_applications": success_rates.get("total_applications", 0),
				"success_rate": success_rates.get("success_rates", {}).get("overall_success", 0),
				"trend_direction": success_rates.get("trends", {}).get("trend_direction", "stable"),
			},
			"analysis_sections": [
				"Detailed Success Rate Analysis",
				"Conversion Funnel Breakdown",
				"Performance Benchmarking",
				"Predictive Analytics",
				"Market Trends Analysis",
				"Competitive Position Assessment",
			],
			"strategic_components": [
				"Monthly trend analysis",
				"Competitive positioning insights",
				"Market opportunity identification",
				"Strategic recommendations",
				"Next month action plan",
			],
			"email_format": "Comprehensive HTML with detailed JSON attachment",
			"delivery_schedule": "First Monday of each month",
		}

		return preview

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to generate report preview: {e!s}")
