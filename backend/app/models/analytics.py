"""
Analytics model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Analytics(Base):
    """Analytics data storage for career insights and reporting"""
    
    __tablename__ = "analytics"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Analytics type for categorization
    type = Column(String(100), nullable=False, index=True)
    
    # Analytics data stored as JSONB for flexibility
    # Different types will have different data structures:
    #
    # Type: "skill_gap_analysis"
    # {
    #   "analysis_date": "2024-01-15",
    #   "missing_skills": [
    #     {"skill": "React", "frequency": 85, "priority": "high"},
    #     {"skill": "Docker", "frequency": 60, "priority": "medium"}
    #   ],
    #   "market_demand": {
    #     "total_jobs_analyzed": 150,
    #     "user_match_percentage": 72
    #   }
    # }
    #
    # Type: "application_success_rate"
    # {
    #   "period": "2024-01",
    #   "applications_sent": 25,
    #   "responses_received": 8,
    #   "interviews_scheduled": 3,
    #   "offers_received": 1,
    #   "conversion_rates": {
    #     "response_rate": 0.32,
    #     "interview_rate": 0.12,
    #     "offer_rate": 0.04
    #   },
    #   "by_category": {
    #     "frontend": {"sent": 10, "responses": 4},
    #     "backend": {"sent": 15, "responses": 4}
    #   }
    # }
    #
    # Type: "market_trends"
    # {
    #   "analysis_date": "2024-01-15",
    #   "location": "San Francisco",
    #   "role_category": "software_engineer",
    #   "trends": {
    #     "salary_range": {"min": 120000, "max": 180000, "median": 150000},
    #     "top_skills": ["Python", "React", "AWS"],
    #     "growth_rate": 0.15,
    #     "job_availability": "high"
    #   }
    # }
    #
    # Type: "recommendation_performance"
    # {
    #   "date": "2024-01-15",
    #   "recommendations_shown": 5,
    #   "recommendations_applied": 2,
    #   "click_through_rate": 0.8,
    #   "application_rate": 0.4,
    #   "avg_recommendation_score": 0.85
    # }
    data = Column(JSON, nullable=False)
    
    # Generation timestamp
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, type='{self.type}', user_id={self.user_id})>"


# Analytics types for reference
ANALYTICS_TYPES = [
    "skill_gap_analysis",
    "application_success_rate", 
    "market_trends",
    "recommendation_performance",
    "career_progression",
    "salary_analysis",
    "company_response_times",
    "application_timing_analysis",
    "job_search_velocity",
    "interview_success_rate"
]