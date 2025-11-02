from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.saved_search import SavedSearch
from app.schemas.saved_search import SavedSearchCreate, SavedSearchUpdate, SavedSearchResponse
import uuid

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


@router.get("/", response_model=List[SavedSearchResponse])
async def get_saved_searches(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get all saved searches for the current user"""
	searches_result = await db.execute(select(SavedSearch).where(SavedSearch.user_id  ==  current_user.id).order_by(SavedSearch.last_used.desc()))
	searches = searches_result.scalars().all()

	return searches


@router.post("/", response_model=SavedSearchResponse)
async def create_saved_search(search_data: SavedSearchCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Create a new saved search"""

	# If this is set as default, unset other defaults
	if search_data.is_default:
		# Update operation - fetch and update

		result = await db.execute(select(SavedSearch).where(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)))

		items = result.scalars().all()

		for item in items:

		    for key, value in {"is_default": False}.items():

		        setattr(item, key, value)

	# Create new saved search
	search = SavedSearch(
		id=str(uuid.uuid4()), user_id=current_user.id, name=search_data.name, filters=search_data.filters, is_default=search_data.is_default
	)

	db.add(search)
	await db.commit()
	await db.refresh(search)

	return search


@router.patch("/{search_id}/last-used")
async def update_search_last_used(search_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Update the last used timestamp for a saved search"""

	result = await db.execute(select(SavedSearch).where(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)))


	search = result.scalar_one_or_none()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# Update last_used timestamp (will be set automatically by onupdate)
	search.last_used = db.execute("SELECT NOW()").scalar()
	await db.commit()

	return {"success": True, "message": "Last used timestamp updated"}


@router.patch("/{search_id}/toggle-default")
async def toggle_default_search(search_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Toggle the default status of a saved search"""

	result = await db.execute(select(SavedSearch).where(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)))


	search = result.scalar_one_or_none()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# If setting as default, unset other defaults
	if not search.is_default:
		# Update operation - fetch and update

		result = await db.execute(select(SavedSearch).where(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)))

		items = result.scalars().all()

		for item in items:

		    for key, value in {"is_default": False}.items():

		        setattr(item, key, value)

	# Toggle the default status
	search.is_default = not search.is_default
	await db.commit()

	return {"success": True, "is_default": search.is_default}


@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
	search_id: str, search_data: SavedSearchUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Update a saved search"""

	result = await db.execute(select(SavedSearch).where(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)))


	search = result.scalar_one_or_none()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# If setting as default, unset other defaults
	if search_data.is_default and not search.is_default:
		# Update operation - fetch and update

		result = await db.execute(select(SavedSearch).where(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)))

		items = result.scalars().all()

		for item in items:

		    for key, value in {"is_default": False}.items():

		        setattr(item, key, value)

	# Update fields
	update_data = search_data.dict(exclude_unset=True)
	for field, value in update_data.items():
		setattr(search, field, value)

	await db.commit()
	await db.refresh(search)

	return search


@router.delete("/{search_id}")
async def delete_saved_search(search_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Delete a saved search"""

	result = await db.execute(select(SavedSearch).where(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)))


	search = result.scalar_one_or_none()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	db.delete(search)
	await db.commit()

	return {"success": True, "message": "Saved search deleted"}
