"""
Google Calendar Service
Handles Google Calendar API integration for event management
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.calendar import CalendarCredential, CalendarEvent

logger = logging.getLogger(__name__)


class GoogleCalendarService:
	"""Google Calendar integration service"""

	def __init__(self, db: Session = None):
		"""
		Initialize Google Calendar service.

		Args:
		    db: Database session for credential storage
		"""
		self.db = db
		self.settings = get_settings()
		self.scopes = ["https://www.googleapis.com/auth/calendar.events"]

	def get_authorization_url(self, redirect_uri: str, state: str = None) -> tuple[str, str]:
		"""
		Generate Google OAuth2 authorization URL.

		Args:
		    redirect_uri: OAuth redirect URI
		    state: Optional state parameter for CSRF protection

		Returns:
		    Tuple of (authorization_url, state)
		"""
		try:
			flow = Flow.from_client_config(
				{
					"web": {
						"client_id": self.settings.google_client_id,
						"client_secret": self.settings.google_client_secret,
						"auth_uri": "https://accounts.google.com/o/oauth2/auth",
						"token_uri": "https://oauth2.googleapis.com/token",
					}
				},
				scopes=self.scopes,
				redirect_uri=redirect_uri,
			)

			auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent", state=state)

			return auth_url, state

		except Exception as e:
			logger.error(f"Error generating Google auth URL: {e!s}")
			raise

	def exchange_code_for_tokens(self, code: str, redirect_uri: str, user_id: int) -> CalendarCredential:
		"""
		Exchange authorization code for access/refresh tokens.

		Args:
		    code: Authorization code from OAuth callback
		    redirect_uri: OAuth redirect URI (must match auth request)
		    user_id: User ID to associate credentials with

		Returns:
		    CalendarCredential object
		"""
		try:
			flow = Flow.from_client_config(
				{
					"web": {
						"client_id": self.settings.google_client_id,
						"client_secret": self.settings.google_client_secret,
						"auth_uri": "https://accounts.google.com/o/oauth2/auth",
						"token_uri": "https://oauth2.googleapis.com/token",
					}
				},
				scopes=self.scopes,
				redirect_uri=redirect_uri,
			)

			flow.fetch_token(code=code)
			credentials = flow.credentials

			# Store credentials in database
			calendar_creds = CalendarCredential(
				user_id=user_id,
				provider="google",
				access_token=credentials.token,
				refresh_token=credentials.refresh_token,
				token_expiry=credentials.expiry,
			)

			if self.db:
				self.db.add(calendar_creds)
				self.db.commit()
				self.db.refresh(calendar_creds)

			return calendar_creds

		except Exception as e:
			logger.error(f"Error exchanging code for tokens: {e!s}")
			if self.db:
				self.db.rollback()
			raise

	def _get_credentials(self, user_id: int) -> Optional[Credentials]:
		"""
		Get valid Google credentials for user.

		Args:
		    user_id: User ID

		Returns:
		    Google Credentials object or None
		"""
		if not self.db:
			return None

		creds_record = (
			self.db.query(CalendarCredential)
			.filter(
				CalendarCredential.user_id == user_id,
				CalendarCredential.provider == "google",
			)
			.first()
		)

		if not creds_record:
			return None

		credentials = Credentials(
			token=creds_record.access_token,
			refresh_token=creds_record.refresh_token,
			token_uri="https://oauth2.googleapis.com/token",
			client_id=self.settings.google_client_id,
			client_secret=self.settings.google_client_secret,
			scopes=self.scopes,
		)

		# Refresh if expired
		if credentials.expired and credentials.refresh_token:
			try:
				credentials.refresh(Request())
				# Update stored tokens
				creds_record.access_token = credentials.token
				creds_record.token_expiry = credentials.expiry
				self.db.commit()
			except Exception as e:
				logger.error(f"Error refreshing Google credentials: {e!s}")
				return None

		return credentials

	def create_event(
		self,
		user_id: int,
		summary: str,
		start_time: datetime,
		end_time: datetime,
		description: str = None,
		location: str = None,
		reminders: List[int] = None,
	) -> Optional[Dict[str, Any]]:
		"""
		Create calendar event.

		Args:
		    user_id: User ID
		    summary: Event title
		    start_time: Event start time
		    end_time: Event end time
		    description: Event description
		    location: Event location
		    reminders: List of reminder minutes before event [15, 60, 1440]

		Returns:
		    Created event data or None
		"""
		credentials = self._get_credentials(user_id)
		if not credentials:
			logger.warning(f"No valid credentials for user {user_id}")
			return None

		try:
			service = build("calendar", "v3", credentials=credentials)

			event_data = {
				"summary": summary,
				"start": {
					"dateTime": start_time.isoformat(),
					"timeZone": "UTC",
				},
				"end": {
					"dateTime": end_time.isoformat(),
					"timeZone": "UTC",
				},
			}

			if description:
				event_data["description"] = description

			if location:
				event_data["location"] = location

			# Add reminders
			if reminders:
				event_data["reminders"] = {
					"useDefault": False,
					"overrides": [{"method": "popup", "minutes": minutes} for minutes in reminders],
				}

			event = service.events().insert(calendarId="primary", body=event_data).execute()

			logger.info(f"Created Google Calendar event: {event.get('id')}")
			return event

		except HttpError as e:
			logger.error(f"Google Calendar API error: {e!s}")
			return None
		except Exception as e:
			logger.error(f"Error creating calendar event: {e!s}")
			return None

	def list_events(
		self,
		user_id: int,
		time_min: datetime = None,
		time_max: datetime = None,
		max_results: int = 10,
	) -> List[Dict[str, Any]]:
		"""
		List calendar events for user.

		Args:
		    user_id: User ID
		    time_min: Start of time range
		    time_max: End of time range
		    max_results: Maximum number of events to return

		Returns:
		    List of event dictionaries
		"""
		credentials = self._get_credentials(user_id)
		if not credentials:
			logger.warning(f"No valid credentials for user {user_id}")
			return []

		try:
			service = build("calendar", "v3", credentials=credentials)

			# Default to next 30 days
			if not time_min:
				time_min = datetime.utcnow()
			if not time_max:
				time_max = time_min + timedelta(days=30)

			events_result = (
				service.events()
				.list(
					calendarId="primary",
					timeMin=time_min.isoformat() + "Z",
					timeMax=time_max.isoformat() + "Z",
					maxResults=max_results,
					singleEvents=True,
					orderBy="startTime",
				)
				.execute()
			)

			events = events_result.get("items", [])
			logger.info(f"Retrieved {len(events)} events for user {user_id}")
			return events

		except HttpError as e:
			logger.error(f"Google Calendar API error: {e!s}")
			return []
		except Exception as e:
			logger.error(f"Error listing calendar events: {e!s}")
			return []

	def update_event(
		self,
		user_id: int,
		event_id: str,
		summary: str = None,
		start_time: datetime = None,
		end_time: datetime = None,
		description: str = None,
		location: str = None,
	) -> Optional[Dict[str, Any]]:
		"""
		Update calendar event.

		Args:
		    user_id: User ID
		    event_id: Event ID to update
		    summary: New event title
		    start_time: New start time
		    end_time: New end time
		    description: New description
		    location: New location

		Returns:
		    Updated event data or None
		"""
		credentials = self._get_credentials(user_id)
		if not credentials:
			return None

		try:
			service = build("calendar", "v3", credentials=credentials)

			# Get existing event
			event = service.events().get(calendarId="primary", eventId=event_id).execute()

			# Update fields
			if summary:
				event["summary"] = summary
			if start_time:
				event["start"] = {
					"dateTime": start_time.isoformat(),
					"timeZone": "UTC",
				}
			if end_time:
				event["end"] = {
					"dateTime": end_time.isoformat(),
					"timeZone": "UTC",
				}
			if description:
				event["description"] = description
			if location:
				event["location"] = location

			updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()

			logger.info(f"Updated Google Calendar event: {event_id}")
			return updated_event

		except HttpError as e:
			logger.error(f"Google Calendar API error: {e!s}")
			return None
		except Exception as e:
			logger.error(f"Error updating calendar event: {e!s}")
			return None

	def delete_event(self, user_id: int, event_id: str) -> bool:
		"""
		Delete calendar event.

		Args:
		    user_id: User ID
		    event_id: Event ID to delete

		Returns:
		    True if successful, False otherwise
		"""
		credentials = self._get_credentials(user_id)
		if not credentials:
			return False

		try:
			service = build("calendar", "v3", credentials=credentials)
			service.events().delete(calendarId="primary", eventId=event_id).execute()

			logger.info(f"Deleted Google Calendar event: {event_id}")
			return True

		except HttpError as e:
			logger.error(f"Google Calendar API error: {e!s}")
			return False
		except Exception as e:
			logger.error(f"Error deleting calendar event: {e!s}")
			return False
