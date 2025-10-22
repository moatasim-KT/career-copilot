"""Skill gap analysis endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.skill_gap_analyzer import SkillGapAnalyzer

router = APIRouter(tags=["skill-gap"])


@router.get("/api/v1/skill-gap", response_model=SkillGapAnalysisResponse)
async def analyze_skill_gap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user's skill gaps based on job market"""
    analyzer = SkillGapAnalyzer(db=db)
    analysis = analyzer.analyze_skill_gaps(current_user)
    return analysis
