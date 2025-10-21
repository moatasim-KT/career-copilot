"""
Enhanced Gmail Service with OAuth2, reliability, and advanced features.
Provides robust Gmail integration with proper authentication and rate limiting.
"""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from pydantic import BaseModel, Field, EmailStr, validator
import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from .email_analytics_service import EmailAnalyticsService, EmailStatus, EmailEventType

logger = get_logger(__name__)


class GmailScope(str, Enum):
    """Gmail API scopes"""
    SEND = "https://www.googleapis.com/auth/gmail.send"
    READONLY = "https://www.googleapis.com/auth/gmail.readonly"
    MODIFY = "https://www.googleapis.com/auth/gmail.modify"
    FULL_ACCESS = "https://www.googleapis.com/auth/gmail"


class GmailConfiguration(BaseModel):
    """Gmail service configuration"""
    client_id: str = Field(..., description="OAuth2 client ID")
    client_secret: str = Field(..., description="OAuth2 client secret")
    redirect_uri: str = Field("http://localhost:8080/callback", description="OAuth2 redirect URI")
    scopes: List[GmailScope] = Field([GmailScope.SEND], description="Required scopes")
    credentials_file: Optional[str] = Field(None, description="Path to credentials file")
    token_file: Optional[str] = Field("gmail_token.json", description="Path to token file")
    rate_limit_per_day: int = Field(1000000000, description="Daily rate limit")
    rate_limit_per_second: int = Field(250, description="Per-second rate limit")
    batch_size: int = Field(100, description="Batch processing size")
    timeout: float = Field(30.0, description="Request timeout")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries")


class GmailMessage(BaseModel):
    """Gmail message model"""
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    cc: List[EmailStr] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailStr] = Field(default_factory=list, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Attachments")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    thread_id: Optional[str] = Field(None, description="Thread ID for replies")
    label_ids: List[str] = Field(default_factory=list, description="Label IDs to apply")
    tracking_enabled: bool = Field(True, description="Enable tracking")


@dataclass
class GmailRateLimiter:
    """Gmail API rate limiter"""
    daily_requests: List[datetime]
    second_requests: List[datetime]
    daily_limit: int
    second_limit: int
    
    def __post_init__(self):
        self.daily_requests = []
        self.second_requests = []


class EnhancedGmailService:
    """Enhanced Gmail service with OAuth2 and advanced features"""
    
    def __init__(self, config: GmailConfiguration):
        self.config = config
        self.credentials: Optional[Credentials] = None
        self.service = None
        self.rate_limiter = GmailRateLimiter(
            daily_requests=[],
            second_requests=[],
            daily_limit=config.rate_limit_per_day,
            second_limit=config.rate_limit_per_second
        )
        self.analytics_service = EmailAnalyticsService()
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize Gmail service with authentication"""
        logger.info("Initializing Enhanced Gmail service...")
        
        try:
            # Load or create credentials
            await self._setup_credentials()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test connection
            await self._test_connection()
            
            self.is_initialized = True
            logger.info("Enhanced Gmail service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise EmailServiceError(f"Gmail initialization failed: {e}")
    
    async def _setup_credentials(self):
        """Setup OAuth2 credentials"""
        # Try to load existing credentials
        if self.config.token_file:
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    self.config.token_file,
                    [scope.value for scope in self.config.scopes]
                )
            except Exception as e:
                logger.warning(f"Could not load existing credentials: {e}")
        
        # Refresh credentials if needed
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                await self._save_credentials()
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                self.credentials = None
        
        # Create new credentials if needed
        if not self.credentials or not self.credentials.valid:
            await self._create_new_credentials()
    
    async def _create_new_credentials(self):
        """Create new OAuth2 credentials"""
        if not self.config.credentials_file:
            raise EmailServiceError("No credentials file provided for Gmail OAuth2")
        
        flow = Flow.from_client_secrets_file(
            self.config.credentials_file,
            scopes=[scope.value for scope in self.config.scopes],
            redirect_uri=self.config.redirect_uri
        )
        
        # Get authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        logger.info(f"Please visit this URL to authorize the application: {auth_url}")
        
        # In a real implementation, you would handle the OAuth2 flow properly
        # For now, we'll assume credentials are provided
        raise EmailServiceError(
            "Gmail OAuth2 setup required. Please complete the OAuth2 flow and provide valid credentials."
        )
    
    async def _save_credentials(self):
        """Save credentials to file"""
        if self.credentials and self.config.token_file:
            try:
                with open(self.config.token_file, 'w') as token_file:
                    token_file.write(self.credentials.to_json())
            except Exception as e:
                logger.error(f"Failed to save credentials: {e}")
    
    async def send_email(self, message: GmailMessage) -> Dict[str, Any]:
        """Send email via Gmail API"""
        if not self.is_initialized:
            await self.initialize()
        
        # Check rate limits
        if not await self._check_rate_limits():
            raise EmailServiceError(
                "Gmail API rate limit exceeded",
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.HIGH
            )
        
        # Generate tracking ID
        tracking_id = self._generate_tracking_id(message)
        
        try:
            # Record send attempt
            await self.analytics_service.record_email_event(
                tracking_id=tracking_id,
                event_type=EmailEventType.SEND,
                recipient=message.to[0] if message.to else "unknown",
                metadata={
                    "subject": message.subject,
                    "recipients_count": len(message.to + message.cc + message.bcc),
                    "has_attachments": len(message.attachments) > 0,
                    "provider": "gmail"
                }
            )
            
            # Send email with retry logic
            result = await self._send_with_retry(message, tracking_id)
            
            # Record successful send
            await self.analytics_service.record_email_event(
                tracking_id=tracking_id,
                event_type=EmailEventType.DELIVERY,
                recipient=message.to[0] if message.to else "unknown",
                metadata=result
            )
            
            return {
                "success": True,
                "tracking_id": tracking_id,
                "message_id": result.get("id"),
                "thread_id": result.get("threadId"),
                "timestamp": datetime.now().isoformat(),
                "provider": "gmail"
            }
            
        except Exception as e:
            # Record failure
            await self.analytics_service.record_email_event(
                tracking_id=tracking_id,
                event_type=EmailEventType.BOUNCE,
                recipient=message.to[0] if message.to else "unknown",
                metadata={"error": str(e), "provider": "gmail"}
            )
            
            logger.error(f"Failed to send Gmail email: {e}")
            raise EmailServiceError(
                f"Gmail email delivery failed: {e}",
                category=ErrorCategory.EXTERNAL_SERVICE,
                severity=ErrorSeverity.HIGH
            )
    
    async def _send_with_retry(self, message: GmailMessage, tracking_id: str) -> Dict[str, Any]:
        """Send email with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await self._send_email_internal(message, tracking_id)
                
            except HttpError as e:
                last_exception = e
                
                # Check if error is retryable
                if e.resp.status in [429, 500, 502, 503, 504]:
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (2 ** attempt)
                        logger.warning(f"Gmail API error {e.resp.status}, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                
                # Non-retryable error
                raise
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Gmail send attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} Gmail send attempts failed")
        
        raise last_exception
    
    async def _send_email_internal(self, message: GmailMessage, tracking_id: str) -> Dict[str, Any]:
        """Internal Gmail email sending logic"""
        # Create MIME message
        mime_message = await self._create_mime_message(message, tracking_id)
        
        # Convert to Gmail API format
        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
        
        # Prepare Gmail API request
        gmail_message = {
            'raw': raw_message
        }
        
        if message.thread_id:
            gmail_message['threadId'] = message.thread_id
        
        if message.label_ids:
            gmail_message['labelIds'] = message.label_ids
        
        # Send via Gmail API
        result = self.service.users().messages().send(
            userId='me',
            body=gmail_message
        ).execute()
        
        # Update rate limiter
        await self._update_rate_limiter()
        
        return result
    
    async def _create_mime_message(self, message: GmailMessage, tracking_id: str) -> MIMEMultipart:
        """Create MIME message for Gmail"""
        # Create message
        if message.body_html and message.body_text:
            mime_message = MIMEMultipart('alternative')
        else:
            mime_message = MIMEMultipart()
        
        # Set headers
        mime_message['From'] = self._format_address(
            message.from_email or "noreply@example.com",
            message.from_name
        )
        mime_message['To'] = ', '.join(message.to)
        if message.cc:
            mime_message['Cc'] = ', '.join(message.cc)
        if message.bcc:
            mime_message['Bcc'] = ', '.join(message.bcc)
        mime_message['Subject'] = message.subject
        
        if message.reply_to:
            mime_message['Reply-To'] = message.reply_to
        
        # Add Gmail-specific headers
        mime_message['X-Mailer'] = 'Career Copilot Enhanced Gmail Service'
        mime_message['X-Tracking-ID'] = tracking_id
        
        # Add custom headers
        for key, value in message.headers.items():
            mime_message[key] = value
        
        # Add body content
        if message.body_text:
            text_part = MIMEText(message.body_text, 'plain', 'utf-8')
            mime_message.attach(text_part)
        
        if message.body_html:
            # Add tracking pixel if enabled
            html_body = message.body_html
            if message.tracking_enabled:
                tracking_pixel = f'<img src="https://track.example.com/gmail/open/{tracking_id}" width="1" height="1" style="display:none;">'
                html_body += tracking_pixel
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            mime_message.attach(html_part)
        
        # Add attachments
        for attachment in message.attachments:
            await self._add_attachment(mime_message, attachment)
        
        return mime_message
    
    async def _add_attachment(self, mime_message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to MIME message"""
        filename = attachment.get('filename', 'attachment')
        content = attachment.get('content', b'')
        content_type = attachment.get('content_type', 'application/octet-stream')
        
        # Gmail attachment size limit (25MB)
        if len(content) > 25 * 1024 * 1024:
            raise EmailServiceError("Attachment too large for Gmail (max 25MB)")
        
        # Create attachment
        part = MIMEBase(*content_type.split('/'))
        part.set_payload(content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        
        mime_message.attach(part)
    
    async def _check_rate_limits(self) -> bool:
        """Check Gmail API rate limits"""
        current_time = datetime.now()
        
        # Clean old requests
        day_ago = current_time - timedelta(days=1)
        second_ago = current_time - timedelta(seconds=1)
        
        self.rate_limiter.daily_requests = [
            req_time for req_time in self.rate_limiter.daily_requests
            if req_time > day_ago
        ]
        
        self.rate_limiter.second_requests = [
            req_time for req_time in self.rate_limiter.second_requests
            if req_time > second_ago
        ]
        
        # Check limits
        if len(self.rate_limiter.daily_requests) >= self.rate_limiter.daily_limit:
            return False
        
        if len(self.rate_limiter.second_requests) >= self.rate_limiter.second_limit:
            return False
        
        return True
    
    async def _update_rate_limiter(self):
        """Update rate limiter with current request"""
        current_time = datetime.now()
        self.rate_limiter.daily_requests.append(current_time)
        self.rate_limiter.second_requests.append(current_time)
    
    async def _test_connection(self):
        """Test Gmail API connection"""
        try:
            # Test by getting user profile
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Gmail connection test successful for {profile.get('emailAddress')}")
        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            raise EmailServiceError(f"Gmail connection test failed: {e}")
    
    def _generate_tracking_id(self, message: GmailMessage) -> str:
        """Generate unique tracking ID"""
        import hashlib
        data = f"gmail_{message.subject}_{message.to[0] if message.to else ''}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _format_address(self, email: str, name: Optional[str] = None) -> str:
        """Format email address with optional name"""
        if name:
            return f"{name} <{email}>"
        return email
    
    async def get_sent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sent messages for analytics"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['SENT'],
                maxResults=limit
            ).execute()
            
            messages = []
            for msg in results.get('messages', []):
                message_detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                messages.append(message_detail)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get sent messages: {e}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            if not self.credentials or not self.credentials.valid:
                return {
                    "healthy": False,
                    "service": "enhanced_gmail",
                    "error": "Invalid or missing credentials",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Test connection
            await self._test_connection()
            
            return {
                "healthy": True,
                "service": "enhanced_gmail",
                "authenticated": True,
                "rate_limits": {
                    "daily_requests": len(self.rate_limiter.daily_requests),
                    "daily_limit": self.rate_limiter.daily_limit,
                    "second_requests": len(self.rate_limiter.second_requests),
                    "second_limit": self.rate_limiter.second_limit
                },
                "scopes": [scope.value for scope in self.config.scopes],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "service": "enhanced_gmail",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def shutdown(self):
        """Shutdown Gmail service"""
        logger.info("Shutting down Enhanced Gmail service...")
        
        # Save credentials if modified
        await self._save_credentials()
        
        self.service = None
        self.credentials = None
        
        logger.info("Enhanced Gmail service shutdown completed")


# Backward compatibility aliases
GmailService = EnhancedGmailService
