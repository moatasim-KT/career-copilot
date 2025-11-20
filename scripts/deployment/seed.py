"""
Main database seeding script
"""
import argparse
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.logging import get_logger
from scripts.database.seeders.user_seeder import seed_users
from scripts.database.seeders.job_seeder import seed_jobs
from scripts.database.seeders.application_seeder import seed_applications
from scripts.database.seeders.precedent_seeder import seed_precedents

logger = get_logger(__name__)

def clear_existing_data(db: Session):
    """Clear all existing data from tables"""
    logger.info("Clearing existing data...")

    try:
        db.execute("DELETE FROM applications")
        db.execute("DELETE FROM jobs")
        db.execute("DELETE FROM users")
        db.commit()
        logger.info("✅ Existing data cleared")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error clearing data: {e}")
        raise

def display_seed_summary(user, jobs, applications):
    """Display summary of seeded data"""
    logger.info("\n" + "=" * 60)
    logger.info("SEED DATA SUMMARY")
    logger.info("=" * 60)
    if user:
        logger.info(f"\nTest User:")
        logger.info(f"  Username: {user.username}")
        logger.info(f"  Email: {user.email}")
        logger.info(f"  Password: password123")
        logger.info(f"  Skills: {', '.join(user.skills)}")
        logger.info(f"  Locations: {', '.join(user.preferred_locations)}")
        logger.info(f"  Experience: {user.experience_level}")

    if jobs:
        logger.info(f"\nJobs Created: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.title} at {job.company} ({job.status})")

    if applications:
        logger.info(f"\nApplications Created: {len(applications)}")
        for app in applications:
            job = next(j for j in jobs if j.id == app.job_id)
            logger.info(f"  - {job.title} at {job.company} - Status: {app.status}")

    logger.info("\n" + "=" * 60)

def main():
    """Main seeding function"""
    parser = argparse.ArgumentParser(description="Seed the database with sample data.")
    parser.add_argument("--all", action="store_true", help="Seed all data.")
    parser.add_argument("--users", action="store_true", help="Seed users.")
    parser.add_argument("--jobs", action="store_true", help="Seed jobs.")
    parser.add_argument("--applications", action="store_true", help="Seed applications.")
    parser.add_argument("--precedents", action="store_true", help="Seed precedents.")
    parser.add_argument("--force", action="store_true", help="Force seeding without confirmation.")
    parser.add_argument("--reset", action="store_true", help="Reset existing data before seeding.")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DATABASE SEEDING SCRIPT")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        if not args.force:
            response = input("\n⚠️  This will clear existing data and create test data. Continue? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Seeding cancelled")
                return

        if args.reset:
            clear_existing_data(db)

        user = None
        jobs = []
        applications = []

        if args.all or args.users:
            user = seed_users(db)
        if args.all or args.jobs:
            if not user:
                user = seed_users(db)
            jobs = seed_jobs(db, user)
        if args.all or args.applications:
            if not user:
                user = seed_users(db)
            if not jobs:
                jobs = seed_jobs(db, user)
            applications = seed_applications(db, user, jobs)
        if args.all or args.precedents:
            import asyncio
            asyncio.run(seed_precedents())

        display_seed_summary(user, jobs, applications)

        logger.info("\n✅ DATABASE SEEDING COMPLETE")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()