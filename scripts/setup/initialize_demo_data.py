"""
Initialize demo data for Career Copilot
Creates a test user with jobs, applications, and skills
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def initialize_demo_data():
	"""Initialize database with demo data"""

	# Create async engine
	engine = create_async_engine(str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://"), echo=False)

	async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

	async with async_session() as db:
		try:
			# Check if demo user exists
			result = await db.execute(select(User).where(User.email == "demo@careercopilot.com"))
			demo_user = result.scalar_one_or_none()

			if not demo_user:
				print("Creating demo user...")
				demo_user = User(
					email="demo@careercopilot.com",
					username="demo_user",
					hashed_password=get_password_hash("demo123"),
					skills=["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"],
					preferred_locations=["Remote", "San Francisco", "New York"],
					experience_level="senior",
					is_admin=False,
				)
				db.add(demo_user)
				await db.flush()
				print(f"✅ Demo user created: {demo_user.email}")
			else:
				print(f"Demo user already exists: {demo_user.email}")

			# Create sample jobs
			result = await db.execute(select(Job).where(Job.user_id == demo_user.id))
			existing_jobs = result.scalars().all()

			if len(existing_jobs) < 5:
				print("Creating sample jobs...")
				sample_jobs = [
					{
						"company": "TechCorp Inc",
						"title": "Senior Backend Engineer",
						"application_url": "https://techcorp.com/careers/senior-backend",
						"location": "Remote",
						"description": "Build scalable backend systems using Python and FastAPI",
						"tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
						"salary_min": 140000,
						"salary_max": 180000,
						"job_type": "full-time",
						"remote_option": "remote",
					},
					{
						"company": "StartupXYZ",
						"title": "Full Stack Developer",
						"application_url": "https://startupxyz.com/jobs/fullstack",
						"location": "San Francisco, CA",
						"description": "Work on exciting projects with React and Node.js",
						"tech_stack": ["React", "Node.js", "TypeScript", "MongoDB", "AWS"],
						"salary_min": 120000,
						"salary_max": 160000,
						"job_type": "full-time",
						"remote_option": "hybrid",
					},
					{
						"company": "Enterprise Solutions Ltd",
						"title": "Tech Lead - Platform Engineering",
						"application_url": "https://enterprise.com/careers/tech-lead",
						"location": "New York, NY",
						"description": "Lead platform engineering team building cloud infrastructure",
						"tech_stack": ["Python", "Go", "Kubernetes", "AWS", "Terraform"],
						"salary_min": 160000,
						"salary_max": 200000,
						"job_type": "full-time",
						"remote_option": "hybrid",
					},
					{
						"company": "DataDriven AI",
						"title": "Machine Learning Engineer",
						"application_url": "https://datadriven.ai/jobs/ml-engineer",
						"location": "Remote",
						"description": "Build ML models and deployment pipelines",
						"tech_stack": ["Python", "PyTorch", "TensorFlow", "MLflow", "Docker"],
						"salary_min": 130000,
						"salary_max": 170000,
						"job_type": "full-time",
						"remote_option": "remote",
					},
					{
						"company": "Cloud Innovations",
						"title": "DevOps Engineer",
						"application_url": "https://cloudinnovations.io/careers/devops",
						"location": "Austin, TX",
						"description": "Manage cloud infrastructure and CI/CD pipelines",
						"tech_stack": ["Kubernetes", "Docker", "Jenkins", "AWS", "Ansible"],
						"salary_min": 110000,
						"salary_max": 150000,
						"job_type": "full-time",
						"remote_option": "onsite",
					},
				]

				for job_data in sample_jobs:
					job = Job(user_id=demo_user.id, **job_data, created_at=datetime.utcnow() - timedelta(days=5))
					db.add(job)

				await db.flush()
				print(f"✅ Created {len(sample_jobs)} sample jobs")

			# Create sample applications
			result = await db.execute(select(Job).where(Job.user_id == demo_user.id).limit(3))
			jobs_for_applications = result.scalars().all()

			if jobs_for_applications:
				result = await db.execute(select(Application).where(Application.user_id == demo_user.id))
				existing_apps = result.scalars().all()

				if len(existing_apps) < 3:
					print("Creating sample applications...")
					statuses = ["applied", "interview", "applied"]

					for i, job in enumerate(jobs_for_applications[:3]):
						application = Application(
							user_id=demo_user.id,
							job_id=job.id,
							status=statuses[i],
							applied_date=datetime.utcnow() - timedelta(days=3 - i),
							notes=f"Applied through company website. Interview {['not scheduled', 'scheduled for next week', 'pending'][i]}.",
						)
						db.add(application)

					await db.flush()
					print(f"✅ Created sample applications")

			await db.commit()
			print("\n🎉 Demo data initialization complete!")
			print(f"\nLogin credentials:")
			print(f"  Email: demo@careercopilot.com")
			print(f"  Password: demo123")
			print(f"\n  User ID: {demo_user.id}")
			print(f"  Skills: {', '.join(demo_user.skills or [])}")

		except Exception as e:
			await db.rollback()
			print(f"❌ Error initializing demo data: {e}")
			raise
		finally:
			await engine.dispose()


if __name__ == "__main__":
	print("Initializing Career Copilot demo data...\n")
	asyncio.run(initialize_demo_data())
	asyncio.run(initialize_demo_data())
