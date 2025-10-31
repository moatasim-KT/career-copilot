from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.saved_search import SavedSearch
from app.schemas.saved_search import SavedSearchCreate, SavedSearchUpdate, SavedSearchResponse
import uuid

router = APIRouter()


@router.get("/", response_model=List[SavedSearchResponse])
async def get_saved_searches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get all saved searches for the current user"""
	searches = db.query(SavedSearch).filter(SavedSearch.user_id == current_user.id).order_by(SavedSearch.last_used.desc()).all()

	return searches


@router.post("/", response_model=SavedSearchResponse)
async def create_saved_search(search_data: SavedSearchCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Create a new saved search"""

	# If this is set as default, unset other defaults
	if search_data.is_default:
		db.query(SavedSearch).filter(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)).update({"is_default": False})

	# Create new saved search
	search = SavedSearch(
		id=str(uuid.uuid4()), user_id=current_user.id, name=search_data.name, filters=search_data.filters, is_default=search_data.is_default
	)

	db.add(search)
	db.commit()
	db.refresh(search)

	return search


@router.patch("/{search_id}/last-used")
async def update_search_last_used(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Update the last used timestamp for a saved search"""

	search = db.query(SavedSearch).filter(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)).first()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# Update last_used timestamp (will be set automatically by onupdate)
	search.last_used = db.execute("SELECT NOW()").scalar()
	db.commit()

	return {"success": True, "message": "Last used timestamp updated"}


@router.patch("/{search_id}/toggle-default")
async def toggle_default_search(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Toggle the default status of a saved search"""

	search = db.query(SavedSearch).filter(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)).first()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# If setting as default, unset other defaults
	if not search.is_default:
		db.query(SavedSearch).filter(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)).update({"is_default": False})

	# Toggle the default status
	search.is_default = not search.is_default
	db.commit()

	return {"success": True, "is_default": search.is_default}


@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
	search_id: str, search_data: SavedSearchUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""Update a saved search"""

	search = db.query(SavedSearch).filter(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)).first()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	# If setting as default, unset other defaults
	if search_data.is_default and not search.is_default:
		db.query(SavedSearch).filter(and_(SavedSearch.user_id == current_user.id, SavedSearch.is_default == True)).update({"is_default": False})

	# Update fields
	update_data = search_data.dict(exclude_unset=True)
	for field, value in update_data.items():
		setattr(search, field, value)

	db.commit()
	db.refresh(search)

	return search


@router.delete("/{search_id}")
async def delete_saved_search(search_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Delete a saved search"""

	search = db.query(SavedSearch).filter(and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)).first()

	if not search:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

	db.delete(search)
	db.commit()

	return {"success": True, "message": "Saved search deleted"}
