"""
Celery tasks for analytics generation
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.skill_analysis_service import skill_analysis_service
from app.services.application_analytics_service import application_analytics_service
from app.services.market_analysis_service import market_analysis_service
from app.celery import celery_app


@celery_app.task(name="generate_skill_gap_analysis")
def generate_skill_gap_analysis():
    """Generate skill gap analysis for all users"""
    db = next(get_db())
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        analyses_generated = 0
        for user in users:
            try:
                analysis = skill_analysis_service.analyze_skill_gap(db, user.id)
                if 'error' not in analysis:
                    skill_analysis_service.save_analysis(db, user.id, analysis)
                    analyses_generated += 1
            except Exception as e:
                print(f"Failed to generate skill analysis for user {user.id}: {e}")
        
        print(f"Generated skill gap analyses for {analyses_generated} users")
        return {'analyses_generated': analyses_generated}
    finally:
        db.close()


@celery_app.task(name="generate_application_analytics")
def generate_application_analytics():
    """Generate application success analytics for all users"""
    db = next(get_db())
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        reports_generated = 0
        for user in users:
            try:
                report = application_analytics_service.get_comprehensive_report(db, user.id)
                if 'error' not in str(report):
                    application_analytics_service.save_analysis(db, user.id, "application_success_rate", report)
                    reports_generated += 1
            except Exception as e:
                print(f"Failed to generate application analytics for user {user.id}: {e}")
        
        print(f"Generated application analytics for {reports_generated} users")
        return {'reports_generated': reports_generated}
    finally:
        db.close()


@celery_app.task(name="generate_market_analysis")
def generate_market_analysis():
    """Generate market trend analysis for all users"""
    db = next(get_db())
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        analyses_generated = 0
        for user in users:
            try:
                dashboard_data = market_analysis_service.create_market_dashboard_data(db, user.id)
                if 'error' not in str(dashboard_data):
                    market_analysis_service.save_analysis(db, user.id, dashboard_data)
                    analyses_generated += 1
            except Exception as e:
                print(f"Failed to generate market analysis for user {user.id}: {e}")
        
        print(f"Generated market analyses for {analyses_generated} users")
        return {'analyses_generated': analyses_generated}
    finally:
        db.close()


@celery_app.task(name="cleanup_old_analytics")
def cleanup_old_analytics():
    """Clean up analytics data older than 90 days"""
    db = next(get_db())
    try:
        from app.models.analytics import Analytics
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=90)
        
        deleted_count = db.query(Analytics).filter(
            Analytics.generated_at < cutoff_date
        ).delete()
        
        db.commit()
        print(f"Cleaned up {deleted_count} old analytics records")
        return {'deleted_count': deleted_count}
    finally:
        db.close()