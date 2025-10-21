from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.dashboard_layout import DashboardLayout
from app.schemas.dashboard_layout import DashboardLayoutCreate, DashboardLayoutUpdate, DashboardLayoutResponse
import uuid

router = APIRouter()

@router.get("/", response_model=List[DashboardLayoutResponse])
async def get_dashboard_layouts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dashboard layouts for the current user"""
    layouts = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).order_by(DashboardLayout.is_default.desc(), DashboardLayout.updated_at.desc()).all()
    
    return layouts

@router.post("/", response_model=DashboardLayoutResponse)
async def create_dashboard_layout(
    layout_data: DashboardLayoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dashboard layout"""
    
    # If this is set as default, unset other defaults
    if layout_data.is_default:
        db.query(DashboardLayout).filter(
            and_(
                DashboardLayout.user_id == current_user.id,
                DashboardLayout.is_default == True
            )
        ).update({"is_default": False})
    
    # Create new dashboard layout
    layout = DashboardLayout(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=layout_data.name,
        widgets=[widget.dict() for widget in layout_data.widgets],
        is_default=layout_data.is_default
    )
    
    db.add(layout)
    db.commit()
    db.refresh(layout)
    
    return layout

@router.put("/{layout_id}", response_model=DashboardLayoutResponse)
async def update_dashboard_layout(
    layout_id: str,
    layout_data: DashboardLayoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a dashboard layout"""
    
    layout = db.query(DashboardLayout).filter(
        and_(
            DashboardLayout.id == layout_id,
            DashboardLayout.user_id == current_user.id
        )
    ).first()
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard layout not found"
        )
    
    # If setting as default, unset other defaults
    if layout_data.is_default and not layout.is_default:
        db.query(DashboardLayout).filter(
            and_(
                DashboardLayout.user_id == current_user.id,
                DashboardLayout.is_default == True
            )
        ).update({"is_default": False})
    
    # Update fields
    update_data = layout_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'widgets' and value is not None:
            setattr(layout, field, [widget.dict() if hasattr(widget, 'dict') else widget for widget in value])
        else:
            setattr(layout, field, value)
    
    db.commit()
    db.refresh(layout)
    
    return layout

@router.patch("/{layout_id}/set-default")
async def set_default_dashboard_layout(
    layout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a dashboard layout as the default"""
    
    layout = db.query(DashboardLayout).filter(
        and_(
            DashboardLayout.id == layout_id,
            DashboardLayout.user_id == current_user.id
        )
    ).first()
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard layout not found"
        )
    
    # Unset other defaults
    db.query(DashboardLayout).filter(
        and_(
            DashboardLayout.user_id == current_user.id,
            DashboardLayout.is_default == True
        )
    ).update({"is_default": False})
    
    # Set this as default
    layout.is_default = True
    db.commit()
    
    return {"success": True, "message": "Dashboard layout set as default"}

@router.delete("/{layout_id}")
async def delete_dashboard_layout(
    layout_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dashboard layout"""
    
    layout = db.query(DashboardLayout).filter(
        and_(
            DashboardLayout.id == layout_id,
            DashboardLayout.user_id == current_user.id
        )
    ).first()
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard layout not found"
        )
    
    # Don't allow deleting the default layout if it's the only one
    if layout.is_default:
        other_layouts = db.query(DashboardLayout).filter(
            and_(
                DashboardLayout.user_id == current_user.id,
                DashboardLayout.id != layout_id
            )
        ).count()
        
        if other_layouts == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only dashboard layout"
            )
        
        # Set another layout as default
        next_layout = db.query(DashboardLayout).filter(
            and_(
                DashboardLayout.user_id == current_user.id,
                DashboardLayout.id != layout_id
            )
        ).first()
        
        if next_layout:
            next_layout.is_default = True
    
    db.delete(layout)
    db.commit()
    
    return {"success": True, "message": "Dashboard layout deleted"}