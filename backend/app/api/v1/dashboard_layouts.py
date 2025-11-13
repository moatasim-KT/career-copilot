import uuid
from typing import List

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.dashboard_layout import DashboardLayout
from app.models.user import User
from app.schemas.dashboard_layout import (DashboardLayoutCreate,
                                          DashboardLayoutResponse,
                                          DashboardLayoutUpdate)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


@router.get("/", response_model=List[DashboardLayoutResponse])
async def get_dashboard_layouts(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get all dashboard layouts for the current user"""
	layouts_result = await db.execute(
		select(DashboardLayout)
		.where(DashboardLayout.user_id == current_user.id)
		.order_by(DashboardLayout.is_default.desc(), DashboardLayout.updated_at.desc())
	)
	layouts = layouts_result.scalars().all()

	return layouts


@router.post("/", response_model=DashboardLayoutResponse)
async def create_dashboard_layout(layout_data: DashboardLayoutCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Create a new dashboard layout"""

	# If this is set as default, unset other defaults
	if layout_data.is_default:
		# Update operation - fetch and update

		result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.user_id == current_user.id, DashboardLayout.is_default == True)))

		items = result.scalars().all()

		for item in items:
			for key, value in {"is_default": False}.items():
				setattr(item, key, value)

	# Create new dashboard layout
	layout = DashboardLayout(
		id=str(uuid.uuid4()),
		user_id=current_user.id,
		name=layout_data.name,
		widgets=[widget.dict() for widget in layout_data.widgets],
		is_default=layout_data.is_default,
	)

	db.add(layout)
	await db.commit()
	await db.refresh(layout)

	return layout


@router.put("/{layout_id}", response_model=DashboardLayoutResponse)
async def update_dashboard_layout(
	layout_id: str, layout_data: DashboardLayoutUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Update a dashboard layout"""

	result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.id == layout_id, DashboardLayout.user_id == current_user.id)))


	layout = result.scalar_one_or_none()

	if not layout:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")

	# If setting as default, unset other defaults
	if layout_data.is_default and not layout.is_default:
		# Update operation - fetch and update

		result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.user_id == current_user.id, DashboardLayout.is_default == True)))

		items = result.scalars().all()

		for item in items:
			for key, value in {"is_default": False}.items():
				setattr(item, key, value)

	# Update fields
	update_data = layout_data.dict(exclude_unset=True)
	for field, value in update_data.items():
		if field == "widgets" and value is not None:
			setattr(layout, field, [widget.dict() if hasattr(widget, "dict") else widget for widget in value])
		else:
			setattr(layout, field, value)

	await db.commit()
	await db.refresh(layout)

	return layout


@router.patch("/{layout_id}/set-default")
async def set_default_dashboard_layout(layout_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Set a dashboard layout as the default"""

	result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.id == layout_id, DashboardLayout.user_id == current_user.id)))


	layout = result.scalar_one_or_none()

	if not layout:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")

	# Unset other defaults
	# Update operation - fetch and update

	result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.user_id == current_user.id, DashboardLayout.is_default == True)))

	items = result.scalars().all()

	for item in items:
		for key, value in {"is_default": False}.items():
			setattr(item, key, value)

	# Set this as default
	layout.is_default = True
	await db.commit()

	return {"success": True, "message": "Dashboard layout set as default"}


@router.delete("/{layout_id}")
async def delete_dashboard_layout(layout_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Delete a dashboard layout"""

	result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.id == layout_id, DashboardLayout.user_id == current_user.id)))


	layout = result.scalar_one_or_none()

	if not layout:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")

	# Don't allow deleting the default layout if it's the only one
	if layout.is_default:
		result = await db.execute(select(func.count()).select_from(DashboardLayout).where(and_(DashboardLayout.user_id == current_user.id, DashboardLayout.id != layout_id)))

		other_layouts = result.scalar() or 0

		if other_layouts == 0:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the only dashboard layout")

		# Set another layout as default
		result = await db.execute(select(DashboardLayout).where(and_(DashboardLayout.user_id == current_user.id, DashboardLayout.id != layout_id)))

		next_layout = result.scalar_one_or_none()

		if next_layout:
			next_layout.is_default = True

	db.delete(layout)
	await db.commit()

	return {"success": True, "message": "Dashboard layout deleted"}
