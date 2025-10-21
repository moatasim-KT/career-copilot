"""
Enhanced SMTP Service with reliability, security, and optimization features.
Provides robust email delivery with connection pooling, retry logic, and security measures.
"""

import asyncio
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import socket
import time
import hashlib
import hmac
import base64

from pydantic import BaseModel, Field, EmailStr, validator
from sqlalchemy import select, and_, func

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import EmailServiceError, ErrorCategory, ErrorSeverity
from .email_analytics_service import EmailAnalyticsService, EmailStatus, EmailEventType

logger = get_logger(__name__)


class SMTPSecurityLevel(str, Enum):
    """SMTP security levels"""
    NONE = "none"           # No encryption
    STARTTLS = "starttls"   # STARTTLS encryption
    SSL_TLS = "ssl_tls"     # SSL/TLS encryption


class SMTPAuthMethod(str, Enum):
    """SMTP authentication methods"""
    PLAIN = "plain"
    LOGIN = "login"
    CRAM_MD5 = "cram_md5"
    OAUTH2 = "oauth2"


@dataclass
class SMTPConnectionPool:
    """SMTP connection pool for reusing connections"""
    host: str
    port: int
    security: SMTPSecurityLevel
    max_connections: int = 10
    active_connections: List[smtplib.SMTP] = field(default_factory=list)
    available_connections: List[smtplib.SMTP] = field(default_factory=list)
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0  # 5 minutes
    last_cleanup: datetime = field(default_factory=datetime.now)


class SMTPConfiguration(BaseModel):
    """SMTP server configuration"""
    host: str = Field(..., description="SMTP server hostname")
    port: int = Field(587, description="SMTP server port")
    security: SMTPSecurityLevel = Field(SMTPSecurityLevel.STARTTLS, description="Security level")
    auth_method: SMTPAuthMethod = Field(SMTPAuthMethod.PLAIN, description="Authentication method")
    username: Optional[str] = Field(None, description="SMTP username")
    password: Optional[str] = Field(None, description="SMTP password")
    timeout: float = Field(30.0, description="Connection timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    connection_pool_size: int = Field(5, description="Connection pool size")
    rate_limit_per_hour: int = Field(1000, description="Rate limit per hour")
    enable_dkim: bool = Field(False, description="Enable DKIM signing")
    dkim_private_key: Optional[str] = Field(None, description="DKIM private key")
    dkim_selector: Optional[str] = Field(None, description="DKIM selector")
    dkim_domain: Optional[str] = Field(None, description="DKIM domain")

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class EmailMessage(BaseModel):
    """Enhanced email message with security and tracking features"""
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    cc: List[EmailStr] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailStr] = Field(default_factory=list, description="BCC recipients")
    subject: str = Field(..., description="Email subject")
    body_text: Optional[str] = Field(None, description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Email attachments")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    priority: str = Field("normal", description="Email priority")
    tracking_enabled: bool = Field(True, description="Enable tracking")
    message_id: Optional[str] = Field(None, description="Custom message ID")
    
    @validator('to', 'cc', 'bcc')
    def validate_recipients(cls, v):
        if isinstance(v, list) and len(v) > 100:
            raise ValueError('Too many recipients (max 100)')
        return v


class EnhancedSMTPService:
    """Enhanced SMTP service with reliability, security, and optimization"""
    
    def __init__(self, config: SMTPConfiguration):
        self.config = config
        self.connection_pools: Dict[str, SMTPConnectionPool] = {}
        self.rate_limiter = {}
        self.analytics_service = EmailAnalyticsService()
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the SMTP service"""
        logger.info("Initializing Enhanced SMTP service...")
        
        # Initialize connection pool
        pool_key = f"{self.config.host}:{self.config.port}"
        self.connection_pools[pool_key] = SMTPConnectionPool(
            host=self.config.host,
            port=self.config.port,
            security=self.config.security,
            max_connections=self.config.connection_pool_size
        )
        
        # Initialize rate limiter
        self.rate_limiter = {
            "requests": [],
            "window_start": time.time()
        }
        
        # Test connection
        await self._test_connection()
        
        self.is_initialized = True
        logger.info("Enhanced SMTP service initialized successfully")
    
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send email with enhanced reliability and tracking"""
        if not self.is_initialized:
            await self.initialize()
        
        # Check rate limiting
        if not await self._check_rate_limit():
            raise EmailServiceError(
                "Rate limit exceeded",
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
                    "has_attachments": len(message.attachments) > 0
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
                "message_id": result.get("message_id"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failure
            await self.analytics_service.record_email_event(
                tracking_id=tracking_id,
                event_type=EmailEventType.BOUNCE,
                recipient=message.to[0] if message.to else "unknown",
                metadata={"error": str(e)}
            )
            
            logger.error(f"Failed to send email: {e}")
            raise EmailServiceError(
                f"Email delivery failed: {e}",
                category=ErrorCategory.EXTERNAL_SERVICE,
                severity=ErrorSeverity.HIGH
            )
    
    async def _send_with_retry(self, message: EmailMessage, tracking_id: str) -> Dict[str, Any]:
        """Send email with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await self._send_email_internal(message, tracking_id)
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Email send attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries + 1} email send attempts failed")
        
        raise last_exception
    
    async def _send_email_internal(self, message: EmailMessage, tracking_id: str) -> Dict[str, Any]:
        """Internal email sending logic"""
        # Get connection from pool
        connection = await self._get_connection()
        
        try:
            # Create MIME message
            mime_message = await self._create_mime_message(message, tracking_id)
            
            # Add DKIM signature if enabled
            if self.config.enable_dkim:
                mime_message = await self._add_dkim_signature(mime_message)
            
            # Send email
            all_recipients = message.to + message.cc + message.bcc
            connection.send_message(mime_message, to_addrs=all_recipients)
            
            # Return connection to pool
            await self._return_connection(connection)
            
            return {
                "message_id": mime_message.get("Message-ID"),
                "recipients": len(all_recipients),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Close connection on error
            await self._close_connection(connection)
            raise
    
    async def _create_mime_message(self, message: EmailMessage, tracking_id: str) -> MIMEMultipart:
        """Create MIME message with security headers and tracking"""
        # Create message
        if message.body_html and message.body_text:
            mime_message = MIMEMultipart('alternative')
        else:
            mime_message = MIMEMultipart()
        
        # Set headers
        mime_message['From'] = self._format_address(
            message.from_email or self.config.username,
            message.from_name
        )
        mime_message['To'] = ', '.join(message.to)
        if message.cc:
            mime_message['Cc'] = ', '.join(message.cc)
        mime_message['Subject'] = message.subject
        mime_message['Date'] = email.utils.formatdate(localtime=True)
        mime_message['Message-ID'] = message.message_id or email.utils.make_msgid()
        
        if message.reply_to:
            mime_message['Reply-To'] = message.reply_to
        
        # Add security headers
        mime_message['X-Mailer'] = 'Career Copilot Enhanced SMTP Service'
        mime_message['X-Priority'] = self._get_priority_header(message.priority)
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
                tracking_pixel = f'<img src="https://track.example.com/open/{tracking_id}" width="1" height="1" style="display:none;">'
                html_body += tracking_pixel
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            mime_message.attach(html_part)
        
        # Add attachments
        for attachment in message.attachments:
            await self._add_attachment(mime_message, attachment)
        
        return mime_message
    
    async def _add_attachment(self, mime_message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to MIME message with security validation"""
        filename = attachment.get('filename', 'attachment')
        content = attachment.get('content', b'')
        content_type = attachment.get('content_type', 'application/octet-stream')
        
        # Security validation
        if len(content) > 25 * 1024 * 1024:  # 25MB limit
            raise EmailServiceError("Attachment too large (max 25MB)")
        
        # Check for dangerous file types
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            raise EmailServiceError(f"Dangerous file type not allowed: {filename}")
        
        # Create attachment
        part = MIMEBase(*content_type.split('/'))
        part.set_payload(content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        
        mime_message.attach(part)
    
    async def _add_dkim_signature(self, mime_message: MIMEMultipart) -> MIMEMultipart:
        """Add DKIM signature to email message"""
        if not all([self.config.dkim_private_key, self.config.dkim_selector, self.config.dkim_domain]):
            logger.warning("DKIM configuration incomplete, skipping signature")
            return mime_message
        
        try:
            # This is a simplified DKIM implementation
            # In production, use a proper DKIM library like dkimpy
            
            # Create DKIM signature headers
            dkim_headers = [
                'from', 'to', 'subject', 'date', 'message-id'
            ]
            
            # Generate signature (simplified)
            signature_data = ""
            for header in dkim_headers:
                if header in mime_message:
                    signature_data += f"{header}:{mime_message[header]}\n"
            
            # Add DKIM-Signature header (simplified)
            mime_message['DKIM-Signature'] = (
                f"v=1; a=rsa-sha256; c=relaxed/relaxed; "
                f"d={self.config.dkim_domain}; s={self.config.dkim_selector}; "
                f"h={':'.join(dkim_headers)}; "
                f"b=<signature_placeholder>"
            )
            
            return mime_message
            
        except Exception as e:
            logger.error(f"DKIM signing failed: {e}")
            return mime_message
    
    async def _get_connection(self) -> smtplib.SMTP:
        """Get SMTP connection from pool"""
        pool_key = f"{self.config.host}:{self.config.port}"
        pool = self.connection_pools[pool_key]
        
        # Clean up idle connections
        await self._cleanup_idle_connections(pool)
        
        # Try to get available connection
        if pool.available_connections:
            connection = pool.available_connections.pop()
            pool.active_connections.append(connection)
            return connection
        
        # Create new connection if under limit
        if len(pool.active_connections) < pool.max_connections:
            connection = await self._create_connection()
            pool.active_connections.append(connection)
            return connection
        
        # Wait for available connection
        for _ in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            if pool.available_connections:
                connection = pool.available_connections.pop()
                pool.active_connections.append(connection)
                return connection
        
        raise EmailServiceError("No SMTP connections available")
    
    async def _create_connection(self) -> smtplib.SMTP:
        """Create new SMTP connection"""
        try:
            if self.config.security == SMTPSecurityLevel.SSL_TLS:
                context = ssl.create_default_context()
                connection = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                    context=context
                )
            else:
                connection = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout
                )
                
                if self.config.security == SMTPSecurityLevel.STARTTLS:
                    connection.starttls()
            
            # Authenticate if credentials provided
            if self.config.username and self.config.password:
                connection.login(self.config.username, self.config.password)
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise EmailServiceError(f"SMTP connection failed: {e}")
    
    async def _return_connection(self, connection: smtplib.SMTP):
        """Return connection to pool"""
        pool_key = f"{self.config.host}:{self.config.port}"
        pool = self.connection_pools[pool_key]
        
        if connection in pool.active_connections:
            pool.active_connections.remove(connection)
            pool.available_connections.append(connection)
    
    async def _close_connection(self, connection: smtplib.SMTP):
        """Close SMTP connection"""
        pool_key = f"{self.config.host}:{self.config.port}"
        pool = self.connection_pools[pool_key]
        
        try:
            connection.quit()
        except:
            pass
        
        if connection in pool.active_connections:
            pool.active_connections.remove(connection)
        if connection in pool.available_connections:
            pool.available_connections.remove(connection)
    
    async def _cleanup_idle_connections(self, pool: SMTPConnectionPool):
        """Clean up idle connections"""
        current_time = datetime.now()
        
        if (current_time - pool.last_cleanup).total_seconds() < 60:
            return  # Only cleanup once per minute
        
        # Close idle connections
        idle_connections = []
        for connection in pool.available_connections:
            try:
                # Test connection
                connection.noop()
            except:
                idle_connections.append(connection)
        
        for connection in idle_connections:
            await self._close_connection(connection)
        
        pool.last_cleanup = current_time
    
    async def _test_connection(self):
        """Test SMTP connection"""
        try:
            connection = await self._create_connection()
            await self._close_connection(connection)
            logger.info("SMTP connection test successful")
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            raise EmailServiceError(f"SMTP connection test failed: {e}")
    
    async def _check_rate_limit(self) -> bool:
        """Check if within rate limits"""
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour window
        
        # Clean old requests
        self.rate_limiter["requests"] = [
            req_time for req_time in self.rate_limiter["requests"]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.rate_limiter["requests"]) >= self.config.rate_limit_per_hour:
            return False
        
        # Add current request
        self.rate_limiter["requests"].append(current_time)
        return True
    
    def _generate_tracking_id(self, message: EmailMessage) -> str:
        """Generate unique tracking ID for email"""
        data = f"{message.subject}{message.to[0] if message.to else ''}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _format_address(self, email: str, name: Optional[str] = None) -> str:
        """Format email address with optional name"""
        if name:
            return f"{name} <{email}>"
        return email
    
    def _get_priority_header(self, priority: str) -> str:
        """Get X-Priority header value"""
        priority_map = {
            "critical": "1 (Highest)",
            "high": "2 (High)",
            "normal": "3 (Normal)",
            "low": "4 (Low)",
            "bulk": "5 (Lowest)"
        }
        return priority_map.get(priority, "3 (Normal)")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            await self._test_connection()
            
            pool_key = f"{self.config.host}:{self.config.port}"
            pool = self.connection_pools.get(pool_key)
            
            return {
                "healthy": True,
                "service": "enhanced_smtp",
                "host": self.config.host,
                "port": self.config.port,
                "security": self.config.security.value,
                "connection_pool": {
                    "active": len(pool.active_connections) if pool else 0,
                    "available": len(pool.available_connections) if pool else 0,
                    "max": pool.max_connections if pool else 0
                },
                "rate_limit": {
                    "current_hour_requests": len(self.rate_limiter.get("requests", [])),
                    "limit": self.config.rate_limit_per_hour
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "service": "enhanced_smtp",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def shutdown(self):
        """Shutdown service and close connections"""
        logger.info("Shutting down Enhanced SMTP service...")
        
        for pool in self.connection_pools.values():
            for connection in pool.active_connections + pool.available_connections:
                await self._close_connection(connection)
        
        self.connection_pools.clear()
        logger.info("Enhanced SMTP service shutdown completed")