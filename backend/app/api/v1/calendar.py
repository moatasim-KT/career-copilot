"""
Calendar Integration API Endpoints
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.calendar import CalendarCredential, CalendarEvent
from app.models.user import User
from app.schemas.calendar import (
	CalendarCredentialCreate,
	CalendarCredentialResponse,
	CalendarEventCreate,
	CalendarEventResponse,
	CalendarEventUpdate,
	CalendarOAuthURL,
)
from app.services.calendar_service import CalendarService

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== OAuth Flow ====================


@router.get("/oauth/{provider}/authorize", response_model=CalendarOAuthURL)
def get_calendar_oauth_url(
	provider: str,
	redirect_uri: str = Query(..., description="OAuth callback redirect URI"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""
	Generate OAuth authorization URL for calendar provider

	Providers: google, outlook
	"""
	if provider not in ["google", "outlook"]:
		raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

	service = CalendarService(db)

	try:
		if provider == "google":
			auth_url = service.get_google_auth_url(current_user.id, redirect_uri)
		else:  # outlook
			auth_url = service.get_outlook_auth_url(current_user.id, redirect_uri)

		return {"auth_url": auth_url, "provider": provider}

	except Exception as e:
		logger.error(f"Error generating {provider} OAuth URL: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {e!s}")


@router.post("/oauth/{provider}/callback", response_model=CalendarCredentialResponse)
def handle_calendar_oauth_callback(
	provider: str,
	code: str = Query(..., description="OAuth authorization code"),
	redirect_uri: str = Query(..., description="OAuth callback redirect URI"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""
	Handle OAuth callback and store calendar credentials
	"""
	if provider not in ["google", "outlook"]:
		raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

	service = CalendarService(db)

	try:
		# Exchange code for tokens
		if provider == "google":
			credentials = service.exchange_google_code(code, redirect_uri)
		else:  # outlook
			credentials = service.exchange_outlook_code(code, redirect_uri)

		# Check if credential already exists
		existing = db.query(CalendarCredential).filter(CalendarCredential.user_id == current_user.id, CalendarCredential.provider == provider).first()

		if existing:
			# Update existing credential
			existing.access_token = credentials["access_token"]
			existing.refresh_token = credentials.get("refresh_token")
			existing.token_expiry = credentials.get("token_expiry")
			existing.is_active = True
			db.commit()
			db.refresh(existing)
			return existing
		else:
			# Create new credential
			new_credential = CalendarCredential(
				user_id=current_user.id,
				provider=provider,
				access_token=credentials["access_token"],
				refresh_token=credentials.get("refresh_token"),
				token_expiry=credentials.get("token_expiry"),
				is_active=True,
			)
			db.add(new_credential)
			db.commit()
			db.refresh(new_credential)
			return new_credential

	except Exception as e:
		logger.error(f"Error handling {provider} OAuth callback: {e}")
		raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e!s}")


@router.delete("/credentials/{provider}")
def disconnect_calendar(
	provider: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Disconnect calendar provider"""
	credential = db.query(CalendarCredential).filter(CalendarCredential.user_id == current_user.id, CalendarCredential.provider == provider).first()

	if not credential:
		raise HTTPException(status_code=404, detail=f"No {provider} calendar connected")

	credential.is_active = False
	db.commit()

	return {"message": f"{provider.capitalize()} calendar disconnected successfully"}


# ==================== Calendar Events ====================


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
	event_data: CalendarEventCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""
	Create a new calendar event

	Automatically syncs to connected calendar provider
	"""
	# Get calendar credential
	credential = (
		db.query(CalendarCredential)
		.filter(
			CalendarCredential.user_id == current_user.id,
			CalendarCredential.provider == event_data.provider,
			CalendarCredential.is_active == True,
		)
		.first()
	)

	if not credential:
		raise HTTPException(status_code=404, detail=f"No active {event_data.provider} calendar connected")

	service = CalendarService(db)

	try:
		# Create event in calendar provider
		calendar_event_data = {
			"title": event_data.title,
			"description": event_data.description,
			"location": event_data.location,
			"start_time": event_data.start_time.isoformat(),
			"end_time": event_data.end_time.isoformat(),
			"timezone": event_data.timezone,
			"reminder_15min": 15 if event_data.reminder_15min else None,
			"reminder_1hour": 60 if event_data.reminder_1hour else None,
			"attendees": event_data.attendees,
		}

		if event_data.provider == "google":
			result = service.create_google_event(credential.access_token, credential.refresh_token, calendar_event_data)
		else:  # outlook
			result = service.create_outlook_event(credential.access_token, calendar_event_data)

		# Store event in database
		new_event = CalendarEvent(
			user_id=current_user.id,
			application_id=event_data.application_id,
			calendar_credential_id=credential.id,
			event_id=result["event_id"],
			title=event_data.title,
			description=event_data.description,
			location=event_data.location,
			start_time=event_data.start_time,
			end_time=event_data.end_time,
			timezone=event_data.timezone,
			reminder_15min=event_data.reminder_15min,
			reminder_1hour=event_data.reminder_1hour,
			reminder_1day=event_data.reminder_1day,
			is_synced=True,
		)

		db.add(new_event)
		db.commit()
		db.refresh(new_event)

		return new_event

	except Exception as e:
		logger.error(f"Error creating calendar event: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {e!s}")


@router.get("/events", response_model=List[CalendarEventResponse])
def get_calendar_events(
	application_id: int = Query(None, description="Filter by application ID"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get user's calendar events"""
	query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)

	if application_id:
		query = query.filter(CalendarEvent.application_id == application_id)

	events = query.order_by(CalendarEvent.start_time.desc()).all()
	return events


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
def get_calendar_event(
	event_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get specific calendar event"""
	event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()

	if not event:
		raise HTTPException(status_code=404, detail="Calendar event not found")

	return event


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
def update_calendar_event(
	event_id: int,
	event_update: CalendarEventUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Update calendar event and sync to provider"""
	event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()

	if not event:
		raise HTTPException(status_code=404, detail="Calendar event not found")

	credential = db.query(CalendarCredential).filter(CalendarCredential.id == event.calendar_credential_id).first()

	if not credential or not credential.is_active:
		raise HTTPException(status_code=400, detail="Calendar credential is no longer active")

	service = CalendarService(db)

	try:
		# Build update data
		update_data = {}
		if event_update.title is not None:
			update_data["title"] = event_update.title
			event.title = event_update.title
		if event_update.description is not None:
			update_data["description"] = event_update.description
			event.description = event_update.description
		if event_update.location is not None:
			update_data["location"] = event_update.location
			event.location = event_update.location
		if event_update.start_time is not None:
			update_data["start_time"] = event_update.start_time.isoformat()
			event.start_time = event_update.start_time
		if event_update.end_time is not None:
			update_data["end_time"] = event_update.end_time.isoformat()
			event.end_time = event_update.end_time

		# Update in calendar provider
		if credential.provider == "google":
			service.update_google_event(credential.access_token, credential.refresh_token, event.event_id, update_data)
		else:  # outlook
			service.update_outlook_event(credential.access_token, event.event_id, update_data)

		db.commit()
		db.refresh(event)

		return event

	except Exception as e:
		logger.error(f"Error updating calendar event: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to update calendar event: {e!s}")


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(
	event_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Delete calendar event from both database and provider"""
	event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()

	if not event:
		raise HTTPException(status_code=404, detail="Calendar event not found")

	credential = db.query(CalendarCredential).filter(CalendarCredential.id == event.calendar_credential_id).first()

	if credential and credential.is_active:
		service = CalendarService(db)
		try:
			# Delete from calendar provider
			if credential.provider == "google":
				service.delete_google_event(credential.access_token, credential.refresh_token, event.event_id)
			else:  # outlook
				service.delete_outlook_event(credential.access_token, event.event_id)
		except Exception as e:
			logger.warning(f"Failed to delete event from provider: {e}")
			# Continue with database deletion even if provider deletion fails

	# Delete from database
	db.delete(event)
	db.commit()

	return None


@router.get("/credentials", response_model=List[CalendarCredentialResponse])
def get_calendar_credentials(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get user's connected calendar providers"""
	credentials = db.query(CalendarCredential).filter(CalendarCredential.user_id == current_user.id).all()
	return credentials
