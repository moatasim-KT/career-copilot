"""
Market Intelligence API endpoints.

Provides real-time job market trends, salary insights, and industry analysis
based on actual job posting data in the database.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, and_, cast, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...core.database import get_db
from ...models.application import Application
from ...models.job import Job
from ...schemas.market import (
	IndustryTrend,
	LocationTrend,
	MarketTrend,
	MarketTrendResponse,
	SalaryInsight,
	SalaryInsightResponse,
	SkillDemand,
	TrendMetric,
)
from ...utils.datetime import utc_now

router = APIRouter(prefix="/market", tags=["Market Intelligence"])


@router.get("/trends", response_model=MarketTrendResponse)
async def get_market_trends(
	time_range: int = Query(default=30, description="Number of days to analyze", ge=7, le=365),
	location: Optional[str] = Query(default=None, description="Filter by location"),
	job_type: Optional[str] = Query(default=None, description="Filter by job type (full-time, contract, etc.)"),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get comprehensive market trends analysis.

	Analyzes job posting data to identify:
	- Posting volume trends
	- Top skills in demand
	- Hot locations
	- Growing industries
	- Remote work trends
	"""
	start_date = utc_now() - timedelta(days=time_range)

	# Base query with filters
	base_query = select(Job).where(Job.created_at >= start_date)

	if location:
		base_query = base_query.where(or_(Job.location.ilike(f"%{location}%"), cast(Job.preferred_locations, String).ilike(f"%{location}%")))

	if job_type:
		base_query = base_query.where(Job.job_type.ilike(f"%{job_type}%"))

	# Total jobs posted in time range
	total_jobs_result = await db.execute(select(func.count(Job.id)).select_from(base_query.subquery()))
	total_jobs = total_jobs_result.scalar() or 0

	# Jobs posted in last 7 days (for trend calculation)
	recent_start = utc_now() - timedelta(days=7)
	recent_jobs_result = await db.execute(select(func.count(Job.id)).where(and_(Job.created_at >= recent_start, Job.created_at >= start_date)))
	recent_jobs = recent_jobs_result.scalar() or 0

	# Calculate growth rate
	previous_period_start = start_date - timedelta(days=time_range)
	previous_jobs_result = await db.execute(
		select(func.count(Job.id)).where(and_(Job.created_at >= previous_period_start, Job.created_at < start_date))
	)
	previous_jobs = previous_jobs_result.scalar() or 1  # Avoid division by zero
	growth_rate = ((total_jobs - previous_jobs) / previous_jobs * 100) if previous_jobs > 0 else 0

	# Top skills analysis
	jobs_result = await db.execute(base_query)
	jobs = jobs_result.scalars().all()

	skill_counts = {}
	for job in jobs:
		if job.tech_stack:
			skills = job.tech_stack if isinstance(job.tech_stack, list) else job.tech_stack.split(",")
			for skill in skills:
				skill = skill.strip()
				if skill:
					skill_counts[skill] = skill_counts.get(skill, 0) + 1

	top_skills = [
		SkillDemand(
			skill=skill,
			demand_count=count,
			growth_percentage=0.0,  # Would need historical data
		)
		for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
	]

	# Location trends
	location_counts = {}
	for job in jobs:
		location = job.location or "Remote"
		location_counts[location] = location_counts.get(location, 0) + 1

	top_locations = [
		LocationTrend(
			location=loc,
			job_count=count,
			avg_salary=0,  # Would calculate from salary data
		)
		for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
	]

	# Remote work percentage
	remote_count = sum(1 for job in jobs if job.remote_option and "remote" in str(job.remote_option).lower())
	remote_percentage = (remote_count / total_jobs * 100) if total_jobs > 0 else 0

	# Company trends
	company_counts = {}
	for job in jobs:
		if job.company:
			company_counts[job.company] = company_counts.get(job.company, 0) + 1

	top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]

	# Industry trends (based on company or job title)
	industry_map = {
		"tech": ["software", "developer", "engineer", "data", "cloud", "ai", "ml"],
		"finance": ["finance", "banking", "fintech", "trading", "investment"],
		"healthcare": ["health", "medical", "pharma", "biotech"],
		"retail": ["retail", "ecommerce", "shopping"],
		"education": ["education", "learning", "training", "university"],
	}

	industry_counts = {industry: 0 for industry in industry_map}
	for job in jobs:
		job_text = f"{job.title} {job.company}".lower()
		for industry, keywords in industry_map.items():
			if any(keyword in job_text for keyword in keywords):
				industry_counts[industry] += 1

	industry_trends = [
		IndustryTrend(
			industry=industry.title(),
			job_count=count,
			growth_rate=0.0,  # Would need historical comparison
		)
		for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)
		if count > 0
	]

	return MarketTrendResponse(
		time_range_days=time_range,
		total_jobs_posted=total_jobs,
		growth_rate=round(growth_rate, 2),
		top_skills=top_skills,
		top_locations=top_locations,
		top_companies=[{"name": name, "job_count": count} for name, count in top_companies],
		industry_trends=industry_trends,
		remote_work_percentage=round(remote_percentage, 2),
		average_postings_per_day=round(total_jobs / time_range, 2) if time_range > 0 else 0,
		generated_at=utc_now(),
	)


@router.get("/salary-insights", response_model=SalaryInsightResponse)
async def get_salary_insights(
	role: Optional[str] = Query(default=None, description="Filter by job role/title"),
	location: Optional[str] = Query(default=None, description="Filter by location"),
	experience_level: Optional[str] = Query(default=None, description="Filter by experience level"),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get comprehensive salary insights and analysis.

	Provides salary statistics by:
	- Job role
	- Location
	- Experience level
	- Industry
	- Company size
	"""

	# Build query with filters
	query = select(Job).where(or_(Job.salary_min.isnot(None), Job.salary_max.isnot(None), Job.salary_range.isnot(None)))

	if role:
		query = query.where(Job.title.ilike(f"%{role}%"))

	if location:
		query = query.where(or_(Job.location.ilike(f"%{location}%"), cast(Job.preferred_locations, String).ilike(f"%{location}%")))

	if experience_level:
		# Would filter by experience_level if we had that field
		pass

	result = await db.execute(query)
	jobs = result.scalars().all()

	if not jobs:
		return SalaryInsightResponse(
			total_data_points=0,
			overall_median=0,
			overall_mean=0,
			overall_min=0,
			overall_max=0,
			by_role=[],
			by_location=[],
			by_experience=[],
			currency_breakdown={"USD": 100.0},
			generated_at=utc_now(),
		)

	# Extract salary data
	salary_data = []
	for job in jobs:
		if job.salary_min and job.salary_max:
			avg_salary = (job.salary_min + job.salary_max) / 2
			salary_data.append({"salary": avg_salary, "role": job.title, "location": job.location, "currency": job.currency or "USD"})
		elif job.salary_min:
			salary_data.append({"salary": job.salary_min, "role": job.title, "location": job.location, "currency": job.currency or "USD"})
		elif job.salary_max:
			salary_data.append({"salary": job.salary_max, "role": job.title, "location": job.location, "currency": job.currency or "USD"})

	if not salary_data:
		return SalaryInsightResponse(
			total_data_points=0,
			overall_median=0,
			overall_mean=0,
			overall_min=0,
			overall_max=0,
			by_role=[],
			by_location=[],
			by_experience=[],
			currency_breakdown={"USD": 100.0},
			generated_at=utc_now(),
		)

	salaries = [d["salary"] for d in salary_data]
	salaries.sort()

	# Overall statistics
	overall_median = salaries[len(salaries) // 2] if salaries else 0
	overall_mean = sum(salaries) / len(salaries) if salaries else 0
	overall_min = min(salaries) if salaries else 0
	overall_max = max(salaries) if salaries else 0

	# By role
	role_salaries = {}
	for data in salary_data:
		role_name = data["role"]
		if role_name not in role_salaries:
			role_salaries[role_name] = []
		role_salaries[role_name].append(data["salary"])

	by_role = [
		SalaryInsight(
			category=role_name,
			median_salary=sorted(sals)[len(sals) // 2],
			mean_salary=sum(sals) / len(sals),
			min_salary=min(sals),
			max_salary=max(sals),
			sample_size=len(sals),
		)
		for role_name, sals in sorted(role_salaries.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)[:10]
	]

	# By location
	location_salaries = {}
	for data in salary_data:
		loc = data["location"] or "Remote"
		if loc not in location_salaries:
			location_salaries[loc] = []
		location_salaries[loc].append(data["salary"])

	by_location = [
		SalaryInsight(
			category=loc,
			median_salary=sorted(sals)[len(sals) // 2],
			mean_salary=sum(sals) / len(sals),
			min_salary=min(sals),
			max_salary=max(sals),
			sample_size=len(sals),
		)
		for loc, sals in sorted(location_salaries.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)[:10]
	]

	# Currency breakdown
	currency_counts = {}
	for data in salary_data:
		currency = data["currency"]
		currency_counts[currency] = currency_counts.get(currency, 0) + 1

	total_currencies = sum(currency_counts.values())
	currency_breakdown = {curr: round(count / total_currencies * 100, 2) for curr, count in currency_counts.items()}

	return SalaryInsightResponse(
		total_data_points=len(salary_data),
		overall_median=round(overall_median, 2),
		overall_mean=round(overall_mean, 2),
		overall_min=round(overall_min, 2),
		overall_max=round(overall_max, 2),
		by_role=by_role,
		by_location=by_location,
		by_experience=[],  # Would need experience level data
		currency_breakdown=currency_breakdown,
		generated_at=utc_now(),
	)
