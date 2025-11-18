"""
Microsoft Outlook Calendar Service
Handles Microsoft Graph API integration for Outlook calendar
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from msal import ConfidentialClientApplication
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.calendar import CalendarCredential

logger = logging.getLogger(__name__)


class MicrosoftCalendarService:
	"""Microsoft Outlook calendar integration service"""

	def __init__(self, db: Session = None):
		"""
		Initialize Microsoft Calendar service.

		Args:
		    db: Database session for credential storage
		"""
		self.db = db
		self.settings = get_settings()
		self.scopes = ["Calendars.ReadWrite"]
		self.graph_endpoint = "https://graph.microsoft.com/v1.0"

	def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
		"""
		Generate Microsoft OAuth2 authorization URL.

		Args:
		    redirect_uri: OAuth redirect URI
		    state: Optional state parameter for CSRF protection

		Returns:
		    Tuple of (authorization_url, state)
		"""
		try:
			app = ConfidentialClientApplication(
				self.settings.microsoft_client_id,
				authority=f"https://login.microsoftonline.com/{self.settings.microsoft_tenant_id}",
				client_credential=self.settings.microsoft_client_secret,
			)

			auth_url = app.get_authorization_request_url(
				scopes=self.scopes,
				redirect_uri=redirect_uri,
				state=state or "",
			)

			return auth_url, state or ""

		except Exception as e:
			logger.error(f"Error generating Microsoft auth URL: {e!s}")
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
			app = ConfidentialClientApplication(
				self.settings.microsoft_client_id,
				authority=f"https://login.microsoftonline.com/{self.settings.microsoft_tenant_id}",
				client_credential=self.settings.microsoft_client_secret,
			)

			result = app.acquire_token_by_authorization_code(
				code=code,
				scopes=self.scopes,
				redirect_uri=redirect_uri,
			)

			if "access_token" not in result:
				raise ValueError(f"Failed to get access token: {result.get('error_description')}")

			# Calculate token expiry
			expires_in = result.get("expires_in", 3600)
			token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

			# Store credentials in database
			calendar_creds = CalendarCredential(
				user_id=user_id,
				provider="microsoft",
				access_token=result["access_token"],
				refresh_token=result.get("refresh_token"),
				token_expiry=token_expiry,
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

	def _get_access_token(self, user_id: int) -> Optional[str]:
		"""
		Get valid access token for user.

		Args:
		    user_id: User ID

		Returns:
		    Access token string or None
		"""
		if not self.db:
			return None

		creds_record = (
			self.db.query(CalendarCredential)
			.filter(
				CalendarCredential.user_id == user_id,
				CalendarCredential.provider == "microsoft",
			)
			.first()
		)

		if not creds_record:
			return None

		# Check if token is expired
		if creds_record.token_expiry and creds_record.token_expiry < datetime.utcnow():
			# Try to refresh
			if creds_record.refresh_token:
				try:
					app = ConfidentialClientApplication(
						self.settings.microsoft_client_id,
						authority=f"https://login.microsoftonline.com/{self.settings.microsoft_tenant_id}",
						client_credential=self.settings.microsoft_client_secret,
					)

					result = app.acquire_token_by_refresh_token(
						refresh_token=creds_record.refresh_token,
						scopes=self.scopes,
					)

					if "access_token" in result:
						creds_record.access_token = result["access_token"]
						expires_in = result.get("expires_in", 3600)
						creds_record.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
						self.db.commit()
					else:
						logger.error("Failed to refresh Microsoft token")
						return None

				except Exception as e:
					logger.error(f"Error refreshing Microsoft token: {e!s}")
					return None

		return creds_record.access_token

	def create_event(
		self,
		user_id: int,
		subject: str,
		start_time: datetime,
		end_time: datetime,
		body: Optional[str] = None,
		location: Optional[str] = None,
		reminders: Optional[List[int]] = None,
	) -> Optional[Dict[str, Any]]:
		"""
		Create Outlook calendar event.

		Args:
		    user_id: User ID
		    subject: Event title
		    start_time: Event start time
		    end_time: Event end time
		    body: Event body/description
		    location: Event location
		    reminders: List of reminder minutes before event

		Returns:
		    Created event data or None
		"""
		access_token = self._get_access_token(user_id)
		if not access_token:
			logger.warning(f"No valid credentials for user {user_id}")
			return None

		try:
			headers = {
				"Authorization": f"Bearer {access_token}",
				"Content-Type": "application/json",
			}

			event_data = {
				"subject": subject,
				"start": {
					"dateTime": start_time.isoformat(),
					"timeZone": "UTC",
				},
				"end": {
					"dateTime": end_time.isoformat(),
					"timeZone": "UTC",
				},
			}

			if body:
				event_data["body"] = {
					"contentType": "text",
					"content": body,
				}

			if location:
				event_data["location"] = {
					"displayName": location,
				}

			# Add reminders
			if reminders:
				event_data["isReminderOn"] = True
				# Microsoft uses first reminder value
				event_data["reminderMinutesBeforeStart"] = reminders[0]

			response = requests.post(
				f"{self.graph_endpoint}/me/events",
				headers=headers,
				json=event_data,
				timeout=30,
			)
			response.raise_for_status()

			event = response.json()
			logger.info(f"Created Microsoft Calendar event: {event.get('id')}")
			return event

		except requests.exceptions.HTTPError as e:
			logger.error(f"Microsoft Graph API error: {e!s}")
			return None
		except Exception as e:
			logger.error(f"Error creating calendar event: {e!s}")
			return None

	def list_events(
		self,
		user_id: int,
		time_min: Optional[datetime] = None,
		time_max: Optional[datetime] = None,
		max_results: int = 10,
	) -> List[Dict[str, Any]]:
		"""
		List Outlook calendar events.

		Args:
		    user_id: User ID
		    time_min: Start of time range
		    time_max: End of time range
		    max_results: Maximum number of events to return

		Returns:
		    List of event dictionaries
		"""
		access_token = self._get_access_token(user_id)
		if not access_token:
			logger.warning(f"No valid credentials for user {user_id}")
			return []

		try:
			headers = {
				"Authorization": f"Bearer {access_token}",
			}

			# Default to next 30 days
			if not time_min:
				time_min = datetime.utcnow()
			if not time_max:
				time_max = time_min + timedelta(days=30)

			params = {
				"$top": max_results,
				"$filter": f"start/dateTime ge '{time_min.isoformat()}' and start/dateTime le '{time_max.isoformat()}'",
				"$orderby": "start/dateTime",
			}

			response = requests.get(
				f"{self.graph_endpoint}/me/events",
				headers=headers,
				params=params,
				timeout=30,
			)
			response.raise_for_status()

			result = response.json()
			events = result.get("value", [])
			logger.info(f"Retrieved {len(events)} events for user {user_id}")
			return events

		except requests.exceptions.HTTPError as e:
			logger.error(f"Microsoft Graph API error: {e!s}")
			return []
		except Exception as e:
			logger.error(f"Error listing calendar events: {e!s}")
			return []

	def update_event(
		self,
		user_id: int,
		event_id: str,
		subject: Optional[str] = None,
		start_time: Optional[datetime] = None,
		end_time: Optional[datetime] = None,
		body: Optional[str] = None,
		location: Optional[str] = None,
	) -> Optional[Dict[str, Any]]:
		"""
		Update Outlook calendar event.

		Args:
		    user_id: User ID
		    event_id: Event ID to update
		    subject: New event title
		    start_time: New start time
		    end_time: New end time
		    body: New body/description
		    location: New location

		Returns:
		    Updated event data or None
		"""
		access_token = self._get_access_token(user_id)
		if not access_token:
			return None

		try:
			headers = {
				"Authorization": f"Bearer {access_token}",
				"Content-Type": "application/json",
			}

			event_data = {}

			if subject:
				event_data["subject"] = subject
			if start_time:
				event_data["start"] = {
					"dateTime": start_time.isoformat(),
					"timeZone": "UTC",
				}
			if end_time:
				event_data["end"] = {
					"dateTime": end_time.isoformat(),
					"timeZone": "UTC",
				}
			if body:
				event_data["body"] = {
					"contentType": "text",
					"content": body,
				}
			if location:
				event_data["location"] = {
					"displayName": location,
				}

			response = requests.patch(
				f"{self.graph_endpoint}/me/events/{event_id}",
				headers=headers,
				json=event_data,
				timeout=30,
			)
			response.raise_for_status()

			event = response.json()
			logger.info(f"Updated Microsoft Calendar event: {event_id}")
			return event

		except requests.exceptions.HTTPError as e:
			logger.error(f"Microsoft Graph API error: {e!s}")
			return None
		except Exception as e:
			logger.error(f"Error updating calendar event: {e!s}")
			return None

	def delete_event(self, user_id: int, event_id: str) -> bool:
		"""
		Delete Outlook calendar event.

		Args:
		    user_id: User ID
		    event_id: Event ID to delete

		Returns:
		    True if successful, False otherwise
		"""
		access_token = self._get_access_token(user_id)
		if not access_token:
			return False

		try:
			headers = {
				"Authorization": f"Bearer {access_token}",
			}

			response = requests.delete(
				f"{self.graph_endpoint}/me/events/{event_id}",
				headers=headers,
				timeout=30,
			)
			response.raise_for_status()

			logger.info(f"Deleted Microsoft Calendar event: {event_id}")
			return True

		except requests.exceptions.HTTPError as e:
			logger.error(f"Microsoft Graph API error: {e!s}")
			return False
		except Exception as e:
			logger.error(f"Error deleting calendar event: {e!s}")
			return False
