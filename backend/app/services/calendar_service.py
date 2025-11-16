"""
Calendar Integration Service
Handles Google Calendar and Microsoft Outlook integration for interview scheduling
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from msal import ConfidentialClientApplication
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class CalendarService:
    """Service for calendar integration with Google Calendar and Outlook"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = settings

    # ==================== Google Calendar ====================

    def get_google_auth_url(self, user_id: int, redirect_uri: str) -> str:
        """Generate Google Calendar OAuth authorization URL"""
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
                scopes=["https://www.googleapis.com/auth/calendar.events"],
                redirect_uri=redirect_uri,
            )

            auth_url, state = flow.authorization_url(
                access_type="offline", include_granted_scopes="true", prompt="consent", state=str(user_id)
            )

            return auth_url

        except Exception as e:
            logger.error(f"Error generating Google auth URL: {e}")
            raise

    def exchange_google_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google OAuth code for access token"""
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
                scopes=["https://www.googleapis.com/auth/calendar.events"],
                redirect_uri=redirect_uri,
            )

            flow.fetch_token(code=code)
            credentials = flow.credentials

            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            }

        except Exception as e:
            logger.error(f"Error exchanging Google code: {e}")
            raise

    def create_google_event(
        self,
        access_token: str,
        refresh_token: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create event in Google Calendar"""
        try:
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
            )

            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            service = build("calendar", "v3", credentials=credentials)

            # Create event structure
            event = {
                "summary": event_data.get("title", "Interview"),
                "description": event_data.get("description", ""),
                "start": {"dateTime": event_data["start_time"], "timeZone": event_data.get("timezone", "UTC")},
                "end": {"dateTime": event_data["end_time"], "timeZone": event_data.get("timezone", "UTC")},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": event_data.get("reminder_15min", 15)},
                        {"method": "email", "minutes": event_data.get("reminder_1hour", 60)},
                    ],
                },
            }

            # Add location if provided
            if "location" in event_data:
                event["location"] = event_data["location"]

            # Add attendees if provided
            if "attendees" in event_data:
                event["attendees"] = [{"email": email} for email in event_data["attendees"]]

            result = service.events().insert(calendarId="primary", body=event).execute()

            return {
                "event_id": result["id"],
                "html_link": result["htmlLink"],
                "status": result["status"],
                "created": result["created"],
            }

        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            raise

    def update_google_event(
        self, access_token: str, refresh_token: str, event_id: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing Google Calendar event"""
        try:
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
            )

            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            service = build("calendar", "v3", credentials=credentials)

            # Get existing event
            event = service.events().get(calendarId="primary", eventId=event_id).execute()

            # Update fields
            if "title" in event_data:
                event["summary"] = event_data["title"]
            if "description" in event_data:
                event["description"] = event_data["description"]
            if "start_time" in event_data:
                event["start"] = {"dateTime": event_data["start_time"], "timeZone": event_data.get("timezone", "UTC")}
            if "end_time" in event_data:
                event["end"] = {"dateTime": event_data["end_time"], "timeZone": event_data.get("timezone", "UTC")}

            result = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()

            return {"event_id": result["id"], "updated": result["updated"], "status": result["status"]}

        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}")
            raise

    def delete_google_event(self, access_token: str, refresh_token: str, event_id: str) -> bool:
        """Delete Google Calendar event"""
        try:
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
            )

            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            service = build("calendar", "v3", credentials=credentials)
            service.events().delete(calendarId="primary", eventId=event_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return False

    # ==================== Microsoft Outlook ====================

    def get_outlook_auth_url(self, user_id: int, redirect_uri: str) -> str:
        """Generate Outlook OAuth authorization URL"""
        try:
            app = ConfidentialClientApplication(
                self.settings.microsoft_client_id,
                authority=f"https://login.microsoftonline.com/{self.settings.microsoft_tenant_id}",
                client_credential=self.settings.microsoft_client_secret,
            )

            auth_url = app.get_authorization_request_url(
                scopes=["https://graph.microsoft.com/Calendars.ReadWrite"],
                redirect_uri=redirect_uri,
                state=str(user_id),
            )

            return auth_url

        except Exception as e:
            logger.error(f"Error generating Outlook auth URL: {e}")
            raise

    def exchange_outlook_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Outlook OAuth code for access token"""
        try:
            app = ConfidentialClientApplication(
                self.settings.microsoft_client_id,
                authority=f"https://login.microsoftonline.com/{self.settings.microsoft_tenant_id}",
                client_credential=self.settings.microsoft_client_secret,
            )

            result = app.acquire_token_by_authorization_code(
                code, scopes=["https://graph.microsoft.com/Calendars.ReadWrite"], redirect_uri=redirect_uri
            )

            if "error" in result:
                raise Exception(f"Outlook token exchange failed: {result.get('error_description')}")

            return {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "token_expiry": (datetime.now() + timedelta(seconds=result["expires_in"])).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exchanging Outlook code: {e}")
            raise

    def create_outlook_event(self, access_token: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Outlook Calendar"""
        import requests

        try:
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            event = {
                "subject": event_data.get("title", "Interview"),
                "body": {"contentType": "HTML", "content": event_data.get("description", "")},
                "start": {
                    "dateTime": event_data["start_time"],
                    "timeZone": event_data.get("timezone", "UTC"),
                },
                "end": {
                    "dateTime": event_data["end_time"],
                    "timeZone": event_data.get("timezone", "UTC"),
                },
                "reminderMinutesBeforeStart": event_data.get("reminder_15min", 15),
            }

            # Add location if provided
            if "location" in event_data:
                event["location"] = {"displayName": event_data["location"]}

            # Add attendees if provided
            if "attendees" in event_data:
                event["attendees"] = [
                    {"emailAddress": {"address": email}, "type": "required"} for email in event_data["attendees"]
                ]

            response = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=event)

            response.raise_for_status()
            result = response.json()

            return {
                "event_id": result["id"],
                "web_link": result["webLink"],
                "created": result["createdDateTime"],
            }

        except Exception as e:
            logger.error(f"Error creating Outlook event: {e}")
            raise

    def update_outlook_event(self, access_token: str, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Outlook Calendar event"""
        import requests

        try:
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Build update payload
            update_data = {}
            if "title" in event_data:
                update_data["subject"] = event_data["title"]
            if "description" in event_data:
                update_data["body"] = {"contentType": "HTML", "content": event_data["description"]}
            if "start_time" in event_data:
                update_data["start"] = {
                    "dateTime": event_data["start_time"],
                    "timeZone": event_data.get("timezone", "UTC"),
                }
            if "end_time" in event_data:
                update_data["end"] = {
                    "dateTime": event_data["end_time"],
                    "timeZone": event_data.get("timezone", "UTC"),
                }

            response = requests.patch(
                f"https://graph.microsoft.com/v1.0/me/events/{event_id}", headers=headers, json=update_data
            )

            response.raise_for_status()
            result = response.json()

            return {"event_id": result["id"], "updated": result["lastModifiedDateTime"]}

        except Exception as e:
            logger.error(f"Error updating Outlook event: {e}")
            raise

    def delete_outlook_event(self, access_token: str, event_id: str) -> bool:
        """Delete Outlook Calendar event"""
        import requests

        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.delete(f"https://graph.microsoft.com/v1.0/me/events/{event_id}", headers=headers)

            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Error deleting Outlook event: {e}")
            return False

    # ==================== Helper Methods ====================

    def get_user_calendar_credentials(self, user_id: int, provider: str) -> Optional[Dict[str, Any]]:
        """Get stored calendar credentials for user"""
        # TODO: Implement database storage for calendar credentials
        # This would query a calendar_credentials table
        pass

    def store_calendar_credentials(self, user_id: int, provider: str, credentials: Dict[str, Any]) -> bool:
        """Store calendar credentials for user"""
        # TODO: Implement database storage for calendar credentials
        # This would insert/update calendar_credentials table
        pass
