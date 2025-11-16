"""
Dashboard Layout API
Manages user's customizable dashboard layouts
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dashboard import DashboardLayout
from app.models.user import User
from app.schemas.dashboard import DashboardLayoutCreate, DashboardLayoutResponse, DashboardLayoutUpdate
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/layout", response_model=DashboardLayoutResponse)
def get_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's dashboard layout configuration"""
    layout = db.query(DashboardLayout).filter(DashboardLayout.user_id == current_user.id).first()

    if not layout:
        # Return default layout if none exists
        return DashboardLayoutResponse(
            id=None,
            user_id=current_user.id,
            layout_config=get_default_layout(),
            is_default=True,
        )

    return layout


@router.post("/layout", response_model=DashboardLayoutResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_dashboard_layout(
    layout_data: DashboardLayoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update user's dashboard layout"""
    # Check if layout exists
    existing = db.query(DashboardLayout).filter(DashboardLayout.user_id == current_user.id).first()

    if existing:
        # Update existing
        existing.layout_config = layout_data.layout_config
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        new_layout = DashboardLayout(user_id=current_user.id, layout_config=layout_data.layout_config)
        db.add(new_layout)
        db.commit()
        db.refresh(new_layout)
        return new_layout


@router.patch("/layout", response_model=DashboardLayoutResponse)
def update_dashboard_layout(
    layout_update: DashboardLayoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update specific widgets in dashboard layout"""
    layout = db.query(DashboardLayout).filter(DashboardLayout.user_id == current_user.id).first()

    if not layout:
        raise HTTPException(status_code=404, detail="Dashboard layout not found. Create one first.")

    # Update layout config
    if layout_update.layout_config:
        layout.layout_config = layout_update.layout_config

    db.commit()
    db.refresh(layout)
    return layout


@router.delete("/layout", status_code=status.HTTP_204_NO_CONTENT)
def reset_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset dashboard to default layout"""
    layout = db.query(DashboardLayout).filter(DashboardLayout.user_id == current_user.id).first()

    if layout:
        db.delete(layout)
        db.commit()

    return None


def get_default_layout() -> Dict[str, Any]:
    """Get default dashboard layout configuration"""
    return {
        "widgets": [
            {"id": "status-overview", "type": "status", "x": 0, "y": 0, "w": 6, "h": 4, "visible": True},
            {"id": "recent-jobs", "type": "jobs", "x": 6, "y": 0, "w": 6, "h": 4, "visible": True},
            {"id": "application-stats", "type": "stats", "x": 0, "y": 4, "w": 6, "h": 4, "visible": True},
            {"id": "upcoming-calendar", "type": "calendar", "x": 6, "y": 4, "w": 6, "h": 4, "visible": True},
            {"id": "recommendations", "type": "recommendations", "x": 0, "y": 8, "w": 12, "h": 4, "visible": True},
            {"id": "activity-timeline", "type": "timeline", "x": 0, "y": 12, "w": 12, "h": 4, "visible": False},
            {"id": "skills-progress", "type": "skills", "x": 0, "y": 16, "w": 6, "h": 4, "visible": False},
            {"id": "goals-tracker", "type": "goals", "x": 6, "y": 16, "w": 6, "h": 4, "visible": False},
        ],
        "columns": 12,
        "rowHeight": 60,
        "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480},
        "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4},
    }
