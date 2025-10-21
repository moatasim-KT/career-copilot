"""
Enhanced DocuSign integration service for contract signing with production-ready features
"""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import hashlib
import hmac

import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.database import get_db_session
from ..repositories.docusign_envelope_repository import DocuSignEnvelopeRepository
from .external_service_manager import get_external_service_manager

logger = get_logger(__name__)


class DocuSignRecipient(BaseModel):
	"""DocuSign recipient model"""
	email: str
	name: str
	role: str = "signer"  # signer, cc, carbon_copy, witness, editor
	routing_order: int = 1
	client_user_id: Optional[str] = None
	recipient_id: Optional[str] = None
	access_code: Optional[str] = None
	id_check_required: bool = False
	phone_authentication: Optional[Dict[str, str]] = None
	sms_authentication: Optional[Dict[str, str]] = None


class DocuSignDocument(BaseModel):
	"""DocuSign document model"""
	document_id: str
	name: str
	file_extension: str
	document_base64: str  # Base64 encoded document content
	transform_pdf_fields: bool = False
	match_boxes: Optional[List[Dict]] = None


class DocuSignTab(BaseModel):
	"""DocuSign tab model for signature placement"""
	tab_type: str = "signHere"  # signHere, dateSign, fullName, company, title, etc.
	document_id: str = "1"
	page_number: str = "1"
	x_position: str = "100"
	y_position: str = "100"
	width: Optional[str] = None
	height: Optional[str] = None
	required: bool = True
	locked: bool = False
	tab_label: Optional[str] = None
	value: Optional[str] = None


class DocuSignEnvelope(BaseModel):
	"""DocuSign envelope model"""
	email_subject: str
	email_blurb: str
	documents: List[DocuSignDocument]
	recipients: List[DocuSignRecipient]
	status: str = "created"  # created, sent, delivered, signed, completed, declined, voided
	custom_fields: Optional[Dict[str, Any]] = None
	notification: Optional[Dict[str, Any]] = None
	enforce_signer_visibility: bool = False
	enable_wet_sign: bool = False
	allow_markup: bool = True
	allow_reassign: bool = True
	brand_id: Optional[str] = None


class DocuSignTemplate(BaseModel):
	"""DocuSign template model"""
	template_id: str
	name: str
	description: Optional[str] = None
	shared: bool = False
	password: Optional[str] = None
	folder_id: Optional[str] = None
	owner: Optional[Dict[str, str]] = None
	created: Optional[datetime] = None
	last_modified: Optional[datetime] = None


class DocuSignWebhookEvent(BaseModel):
	"""DocuSign webhook event model"""
	event: str
	api_version: str
	uri: str
	retry_count: int = 0
	configuration_id: int
	generated_date_time: str
	data: Dict[str, Any]
	envelope_id: Optional[str] = None
	recipient_id: Optional[str] = None


class DocuSignAuditEvent(BaseModel):
	"""DocuSign audit event model"""
	event_timestamp: datetime
	event_description: str
	user_name: Optional[str] = None
	user_id: Optional[str] = None
	client_ip: Optional[str] = None
	geo_location: Optional[Dict[str, str]] = None


class DocuSignError(Exception):
	"""Custom DocuSign error class"""
	def __init__(self, message: str, error_code: Optional[str] = None, status_code: Optional[int] = None):
		self.message = message
		self.error_code = error_code
		self.status_code = status_code
		super().__init__(self.message)


class DocuSignService:
	"""Enhanced DocuSign integration service with production-ready features"""

	def __init__(self):
		self.settings = get_settings()
		self.service_manager = get_external_service_manager()
		
		# Check for sandbox configuration first, then production
		self.sandbox_enabled = getattr(self.settings, "docusign_sandbox_enabled", False)
		self.production_enabled = getattr(self.settings, "docusign_enabled", False)
		
		if self.sandbox_enabled:
			# Use sandbox configuration
			self.client_id = getattr(self.settings, "docusign_sandbox_client_id", "")
			self.client_secret = getattr(self.settings, "docusign_sandbox_client_secret", "")
			self.redirect_uri = getattr(self.settings, "docusign_sandbox_redirect_uri", "")
			self.scopes = getattr(self.settings, "docusign_sandbox_scopes", "signature,impersonation").split(",")
			self.enabled = True
			self.environment = "demo"
		elif self.production_enabled:
			# Use production configuration
			self.client_id = getattr(self.settings, "docusign_client_id", "")
			self.client_secret = getattr(self.settings, "docusign_client_secret", "")
			self.redirect_uri = getattr(self.settings, "docusign_redirect_uri", "")
			self.scopes = getattr(self.settings, "docusign_scopes", ["signature", "impersonation"])
			self.enabled = True
			self.environment = "production"
		else:
			# DocuSign not enabled
			self.client_id = ""
			self.client_secret = ""
			self.redirect_uri = ""
			self.scopes = []
			self.enabled = False
			self.environment = "demo"
		
		self.webhook_secret = getattr(self.settings, "docusign_webhook_secret", "")
		
		# Rate limiting and retry configuration
		self.max_retries = getattr(self.settings, "docusign_max_retries", 3)
		self.retry_delay = getattr(self.settings, "docusign_retry_delay", 1.0)
		self.rate_limit_per_minute = getattr(self.settings, "docusign_rate_limit", 1000)
		
		# Connection timeout settings
		self.timeout = getattr(self.settings, "docusign_timeout", 30.0)
		
		self.access_token = None
		self.refresh_token = None
		self.token_expires_at = None
		self.account_id = None
		self.base_uri = None

		# Environment-specific URLs
		if self.environment == "production":
			self.auth_server_url = "https://account.docusign.com"
			self.base_url = "https://na1.docusign.net/restapi/v2.1"  # Will be updated after auth
		else:
			self.auth_server_url = "https://account-d.docusign.com"
			self.base_url = "https://demo.docusign.net/restapi/v2.1"

		# Template cache
		self._template_cache = {}
		self._template_cache_expiry = None
		
		# Audit trail storage
		self._audit_events = []

		# Register authentication refresh callback
		self.service_manager.auth_manager.register_refresh_callback(
			"docusign", self.refresh_access_token
		)

		logger.info(f"DocuSign service initialized: enabled={self.enabled}, environment={self.environment}")

	def _log_audit_event(self, event_description: str, user_name: Optional[str] = None, 
						 envelope_id: Optional[str] = None, additional_data: Optional[Dict] = None):
		"""Log audit event for compliance tracking"""
		try:
			audit_event = {
				"timestamp": datetime.now().isoformat(),
				"event_description": event_description,
				"user_name": user_name,
				"envelope_id": envelope_id,
				"additional_data": additional_data or {}
			}
			self._audit_events.append(audit_event)
			logger.info(f"DocuSign audit event: {event_description}", extra=audit_event)
		except Exception as e:
			logger.error(f"Failed to log audit event: {e}")

	def _handle_api_error(self, response: httpx.Response, operation: str) -> None:
		"""Handle DocuSign API errors with detailed logging"""
		try:
			error_data = response.json()
			error_code = error_data.get("errorCode", "UNKNOWN")
			error_message = error_data.get("message", "Unknown error")
		except:
			error_code = f"HTTP_{response.status_code}"
			error_message = response.text or "Unknown error"
		
		self._log_audit_event(
			f"API Error in {operation}",
			additional_data={
				"error_code": error_code,
				"error_message": error_message,
				"status_code": response.status_code
			}
		)
		
		raise DocuSignError(
			message=f"{operation} failed: {error_message}",
			error_code=error_code,
			status_code=response.status_code
		)

	@retry(
		stop=stop_after_attempt(3),
		wait=wait_exponential(multiplier=1, min=1, max=10),
		retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, DocuSignError))
	)
	async def _make_api_request(
		self, 
		method: str, 
		url: str, 
		headers: Optional[Dict] = None,
		json_data: Optional[Dict] = None,
		data: Optional[Dict] = None,
		params: Optional[Dict] = None
	) -> httpx.Response:
		"""Make API request with enhanced retry logic and error handling"""
		if not await self._ensure_authenticated():
			raise DocuSignError("Authentication failed", "AUTH_FAILED")
		
		# Store token in service manager for automatic handling
		if self.access_token:
			self.service_manager.auth_manager.store_token(
				"docusign",
				self.access_token,
				self.refresh_token,
				self.token_expires_at
			)
		
		request_headers = {
			"Content-Type": "application/json",
			"User-Agent": "ContractAnalyzer/1.0"
		}
		
		if headers:
			request_headers.update(headers)
		
		try:
			# Use service manager for enhanced request handling
			response = await self.service_manager.make_request(
				service_name="docusign",
				method=method,
				url=url,
				headers=request_headers,
				json_data=json_data,
				data=data,
				params=params,
				timeout=self.timeout,
				require_auth=True
			)
			
			# Handle DocuSign-specific responses
			if response.status_code == 429:
				retry_after = int(response.headers.get("Retry-After", 60))
				logger.warning(f"DocuSign rate limited, retry after {retry_after} seconds")
				raise DocuSignError("Rate limited", "RATE_LIMITED", 429)
			
			if not response.is_success:
				self._handle_api_error(response, f"{method} {url}")
			
			return response
			
		except DocuSignError:
			raise
		except Exception as e:
			logger.error(f"DocuSign API request failed: {e}")
			raise DocuSignError(f"API request failed: {str(e)}", "REQUEST_FAILED")

	def get_authorization_url(self) -> Optional[str]:
		"""Get the DocuSign authorization URL"""
		if not self.enabled:
			return None

		params = {
			"response_type": "code",
			"scope": " ".join(self.scopes),
			"client_id": self.client_id,
			"redirect_uri": self.redirect_uri,
		}
		
		auth_url = f"{self.auth_server_url}/oauth/auth?{urlencode(params)}"
		self._log_audit_event("Authorization URL generated")
		return auth_url

	async def handle_oauth_callback(self, code: str) -> bool:
		"""Handle the OAuth callback from DocuSign with enhanced error handling"""
		if not self.enabled:
			self._log_audit_event("OAuth callback attempted but service disabled")
			return False

		try:
			timeout = httpx.Timeout(self.timeout)
			async with httpx.AsyncClient(timeout=timeout) as client:
				response = await client.post(
					f"{self.auth_server_url}/oauth/token",
					headers={"Content-Type": "application/x-www-form-urlencoded"},
					data={
						"grant_type": "authorization_code",
						"code": code,
						"client_id": self.client_id,
						"client_secret": self.client_secret,
						"redirect_uri": self.redirect_uri,
					},
				)
				
				if not response.is_success:
					error_data = response.json() if response.content else {}
					error_msg = error_data.get("error_description", "OAuth token exchange failed")
					self._log_audit_event(f"OAuth callback failed: {error_msg}")
					logger.error(f"OAuth token exchange failed: {error_msg}")
					return False
				
				token_data = response.json()

				self.access_token = token_data["access_token"]
				self.refresh_token = token_data.get("refresh_token")
				expires_in = token_data.get("expires_in", 3600)
				self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

				# Get user info and account details
				if await self._get_user_info():
					self._log_audit_event("OAuth callback completed successfully")
					logger.info("DocuSign OAuth callback handled successfully")
					return True
				else:
					self._log_audit_event("OAuth callback failed during user info retrieval")
					return False
					
		except httpx.TimeoutException:
			self._log_audit_event("OAuth callback timeout")
			logger.error("DocuSign OAuth callback timeout")
			return False
		except Exception as e:
			self._log_audit_event(f"OAuth callback error: {str(e)}")
			logger.error(f"DocuSign OAuth callback failed: {e}")
			return False

	async def _get_user_info(self) -> bool:
		"""Get user information from DocuSign with enhanced error handling"""
		if not self.access_token:
			return False

		try:
			timeout = httpx.Timeout(self.timeout)
			async with httpx.AsyncClient(timeout=timeout) as client:
				response = await client.get(
					f"{self.auth_server_url}/oauth/userinfo",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				
				if not response.is_success:
					logger.error(f"Failed to get user info: HTTP {response.status_code}")
					return False
				
				user_info = response.json()
				accounts = user_info.get("accounts", [])
				
				if not accounts:
					logger.error("No DocuSign accounts found for user")
					return False
				
				# Use the first account (or find default account)
				account = accounts[0]
				for acc in accounts:
					if acc.get("is_default", False):
						account = acc
						break
				
				self.account_id = account.get("account_id")
				self.base_uri = account.get("base_uri")
				
				if self.account_id and self.base_uri:
					self.base_url = f"{self.base_uri}/restapi/v2.1"
					self._log_audit_event(
						"User info retrieved successfully",
						additional_data={
							"account_id": self.account_id,
							"base_uri": self.base_uri
						}
					)
					return True
				else:
					logger.error("Invalid account information received")
					return False
					
		except Exception as e:
			logger.error(f"Failed to get DocuSign user info: {e}")
			return False

	async def refresh_access_token(self) -> bool:
		"""Refresh the DocuSign access token with enhanced error handling"""
		if not self.refresh_token:
			logger.warning("No refresh token available")
			return False

		try:
			timeout = httpx.Timeout(self.timeout)
			async with httpx.AsyncClient(timeout=timeout) as client:
				response = await client.post(
					f"{self.auth_server_url}/oauth/token",
					headers={"Content-Type": "application/x-www-form-urlencoded"},
					data={
						"grant_type": "refresh_token",
						"refresh_token": self.refresh_token,
						"client_id": self.client_id,
						"client_secret": self.client_secret,
					},
				)
				
				if not response.is_success:
					error_data = response.json() if response.content else {}
					error_msg = error_data.get("error_description", "Token refresh failed")
					self._log_audit_event(f"Token refresh failed: {error_msg}")
					logger.error(f"Failed to refresh token: {error_msg}")
					return False
				
				token_data = response.json()

				self.access_token = token_data["access_token"]
				self.refresh_token = token_data.get("refresh_token", self.refresh_token)
				expires_in = token_data.get("expires_in", 3600)
				self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
				
				self._log_audit_event("Access token refreshed successfully")
				logger.info("DocuSign access token refreshed successfully")
				return True
				
		except Exception as e:
			self._log_audit_event(f"Token refresh error: {str(e)}")
			logger.error(f"Failed to refresh DocuSign access token: {e}")
			return False

	async def _ensure_authenticated(self) -> bool:
		"""Ensure we have a valid access token with buffer time"""
		# Check if token expires within 5 minutes
		buffer_time = timedelta(minutes=5)
		
		if not self.access_token or (
			self.token_expires_at and 
			datetime.now() + buffer_time >= self.token_expires_at
		):
			if self.refresh_token:
				return await self.refresh_access_token()
			else:
				logger.warning("DocuSign access token has expired and no refresh token is available.")
				return False
		return True

	async def create_envelope(self, envelope: DocuSignEnvelope) -> Optional[str]:
		"""Create a DocuSign envelope with enhanced error handling and validation"""
		try:
			# Validate envelope data
			if not envelope.documents:
				raise DocuSignError("Envelope must contain at least one document", "INVALID_ENVELOPE")
			
			if not envelope.recipients:
				raise DocuSignError("Envelope must contain at least one recipient", "INVALID_ENVELOPE")
			
			# Prepare envelope data
			envelope_data = envelope.dict()
			
			# Add default notification settings if not provided
			if not envelope_data.get("notification"):
				envelope_data["notification"] = {
					"useAccountDefaults": True,
					"reminders": {
						"reminderEnabled": True,
						"reminderDelay": 2,
						"reminderFrequency": 2
					},
					"expirations": {
						"expireEnabled": True,
						"expireAfter": 30,
						"expireWarn": 5
					}
				}
			
			# Make API request with retry logic
			response = await self._make_api_request(
				"POST",
				f"{self.base_url}/accounts/{self.account_id}/envelopes",
				json_data=envelope_data
			)
			
			envelope_response = response.json()
			envelope_id = envelope_response["envelopeId"]
			
			self._log_audit_event(
				"Envelope created successfully",
				envelope_id=envelope_id,
				additional_data={
					"subject": envelope.email_subject,
					"recipient_count": len(envelope.recipients),
					"document_count": len(envelope.documents)
				}
			)
			
			logger.info(f"DocuSign: Created envelope {envelope_id}")
			return envelope_id
			
		except DocuSignError:
			raise
		except Exception as e:
			self._log_audit_event(f"Envelope creation failed: {str(e)}")
			logger.error(f"Failed to create DocuSign envelope: {e}")
			raise DocuSignError(f"Envelope creation failed: {str(e)}", "CREATION_FAILED")

	async def send_envelope(self, envelope_id: str) -> bool:
		"""Send a DocuSign envelope for signing"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return False

		try:
			async with httpx.AsyncClient() as client:
				response = await client.put(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}",
					headers={
						"Authorization": f"Bearer {self.access_token}",
						"Content-Type": "application/json",
					},
					json={"status": "sent"},
				)
				response.raise_for_status()
				logger.info(f"DocuSign: Sent envelope {envelope_id}")
				return True
		except Exception as e:
			logger.error(f"Failed to send DocuSign envelope: {e}")
			return False

	async def get_envelope_status(self, envelope_id: str) -> Optional[Dict[str, Any]]:
		"""Get envelope status"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.json()
		except Exception as e:
			logger.error(f"Failed to get DocuSign envelope status: {e}")
			return None

	async def void_envelope(self, envelope_id: str, reason: str) -> bool:
		"""Void a DocuSign envelope"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return False

		try:
			async with httpx.AsyncClient() as client:
				response = await client.put(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}",
					headers={
						"Authorization": f"Bearer {self.access_token}",
						"Content-Type": "application/json",
					},
					json={"status": "voided", "voidedReason": reason},
				)
				response.raise_for_status()
				logger.info(f"DocuSign: Voided envelope {envelope_id}")
				return True
		except Exception as e:
			logger.error(f"Failed to void DocuSign envelope: {e}")
			return False

	async def get_document(self, envelope_id: str, document_id: str) -> Optional[bytes]:
		"""Get document from envelope"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/documents/{document_id}",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.content
		except Exception as e:
			logger.error(f"Failed to get DocuSign document: {e}")
			return None

	async def create_contract_envelope(
		self,
		contract_analysis_id: str,
		contract_name: str,
		contract_content: bytes,
		recipients: List[Dict[str, str]],
		subject: str = "Contract for Signature",
		message: str = "Please review and sign the attached contract.",
	) -> Optional[str]:
		"""Create a contract envelope for signing"""
		try:
			# Encode contract content
			contract_base64 = base64.b64encode(contract_content).decode("utf-8")

			# Create document
			document = DocuSignDocument(document_id="1", name=contract_name, file_extension="pdf", document_base64=contract_base64)

			# Create recipients
			docu_recipients = []
			for i, recipient in enumerate(recipients, 1):
				docu_recipients.append(
					DocuSignRecipient(email=recipient.get("email", ""), name=recipient.get("name", ""), role="signer", routing_order=i)
				)

			# Create envelope
			envelope = DocuSignEnvelope(
				email_subject=subject,
				email_blurb=message,
				documents=[document],
				recipients=docu_recipients,
				custom_fields={"contract_name": contract_name, "created_by": "Career Copilot AI", "analysis_date": datetime.now().isoformat()},
			)

			# Create and send envelope
			envelope_id = await self.create_envelope(envelope)
			if envelope_id:
				await self.send_envelope(envelope_id)
				# Save to database
				async with get_db_session() as db_session:
					envelope_repo = DocuSignEnvelopeRepository(db_session)
					await envelope_repo.create_envelope(
						envelope_id=envelope_id,
						contract_analysis_id=contract_analysis_id,
						status="sent",
						recipients=[recipient.dict() for recipient in docu_recipients],
					)
				return envelope_id

			return None

		except Exception as e:
			logger.error(f"Failed to create contract envelope: {e}")
			return None

	async def get_signing_url(self, envelope_id: str, recipient_email: str, recipient_name: str, return_url: str) -> Optional[str]:
		"""Get signing URL for a recipient"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.post(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/views/recipient",
					headers={
						"Authorization": f"Bearer {self.access_token}",
						"Content-Type": "application/json",
					},
					json={
						"returnUrl": return_url,
						"authenticationMethod": "none",
						"email": recipient_email,
						"userName": recipient_name,
					},
				)
				response.raise_for_status()
				view_data = response.json()
				return view_data["url"]
		except Exception as e:
			logger.error(f"Failed to get signing URL: {e}")
			return None

	async def get_account_info(self) -> Optional[Dict[str, Any]]:
		"""Get DocuSign account information"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.json()
		except Exception as e:
			logger.error(f"Failed to get DocuSign account info: {e}")
			return None

	async def test_connection(self) -> Dict[str, Any]:
		"""Test DocuSign connection"""
		if not self.enabled:
			return {"success": False, "message": "DocuSign is not enabled"}
			
		auth_url = self.get_authorization_url()
		return {
			"success": True,
			"message": "DocuSign is enabled. To authenticate, please navigate to the following URL",
			"authorization_url": auth_url
		}

	async def get_templates(self, use_cache: bool = True) -> List[DocuSignTemplate]:
		"""Get available DocuSign templates with caching"""
		# Check cache first
		if use_cache and self._template_cache and self._template_cache_expiry:
			if datetime.now() < self._template_cache_expiry:
				return self._template_cache.get("templates", [])
		
		try:
			response = await self._make_api_request(
				"GET",
				f"{self.base_url}/accounts/{self.account_id}/templates"
			)
			
			templates_data = response.json()
			raw_templates = templates_data.get("envelopeTemplates", [])
			
			# Convert to DocuSignTemplate objects
			templates = []
			for template_data in raw_templates:
				template = DocuSignTemplate(
					template_id=template_data.get("templateId", ""),
					name=template_data.get("name", ""),
					description=template_data.get("description"),
					shared=template_data.get("shared", False),
					folder_id=template_data.get("folderId"),
					owner=template_data.get("owner"),
					created=self._parse_docusign_date(template_data.get("created")),
					last_modified=self._parse_docusign_date(template_data.get("lastModified"))
				)
				templates.append(template)
			
			# Update cache
			self._template_cache = {"templates": templates}
			self._template_cache_expiry = datetime.now() + timedelta(hours=1)
			
			self._log_audit_event(f"Retrieved {len(templates)} templates")
			return templates
			
		except Exception as e:
			logger.error(f"Failed to get DocuSign templates: {e}")
			return []

	async def create_template(
		self,
		name: str,
		description: str,
		documents: List[DocuSignDocument],
		recipients: List[DocuSignRecipient],
		email_subject: str = "",
		email_blurb: str = ""
	) -> Optional[str]:
		"""Create a new DocuSign template"""
		try:
			template_data = {
				"name": name,
				"description": description,
				"emailSubject": email_subject or f"Please sign: {name}",
				"emailBlurb": email_blurb or f"Please review and sign the {name} document.",
				"documents": [doc.dict() for doc in documents],
				"recipients": {
					"signers": [
						{
							"email": recipient.email,
							"name": recipient.name,
							"recipientId": recipient.recipient_id or str(i + 1),
							"routingOrder": recipient.routing_order,
							"roleName": f"Signer{i + 1}"
						}
						for i, recipient in enumerate(recipients)
					]
				},
				"status": "created"
			}
			
			response = await self._make_api_request(
				"POST",
				f"{self.base_url}/accounts/{self.account_id}/templates",
				json_data=template_data
			)
			
			template_response = response.json()
			template_id = template_response.get("templateId")
			
			if template_id:
				self._log_audit_event(
					f"Template created: {name}",
					additional_data={"template_id": template_id}
				)
				# Clear template cache
				self._template_cache = {}
				self._template_cache_expiry = None
			
			return template_id
			
		except Exception as e:
			logger.error(f"Failed to create DocuSign template: {e}")
			return None

	async def update_template(
		self,
		template_id: str,
		name: Optional[str] = None,
		description: Optional[str] = None,
		email_subject: Optional[str] = None,
		email_blurb: Optional[str] = None
	) -> bool:
		"""Update an existing DocuSign template"""
		try:
			update_data = {}
			
			if name:
				update_data["name"] = name
			if description:
				update_data["description"] = description
			if email_subject:
				update_data["emailSubject"] = email_subject
			if email_blurb:
				update_data["emailBlurb"] = email_blurb
			
			if not update_data:
				return True  # Nothing to update
			
			response = await self._make_api_request(
				"PUT",
				f"{self.base_url}/accounts/{self.account_id}/templates/{template_id}",
				json_data=update_data
			)
			
			self._log_audit_event(
				f"Template updated",
				additional_data={"template_id": template_id, "updates": list(update_data.keys())}
			)
			
			# Clear template cache
			self._template_cache = {}
			self._template_cache_expiry = None
			
			return True
			
		except Exception as e:
			logger.error(f"Failed to update DocuSign template: {e}")
			return False

	async def delete_template(self, template_id: str) -> bool:
		"""Delete a DocuSign template"""
		try:
			response = await self._make_api_request(
				"DELETE",
				f"{self.base_url}/accounts/{self.account_id}/templates/{template_id}"
			)
			
			self._log_audit_event(
				f"Template deleted",
				additional_data={"template_id": template_id}
			)
			
			# Clear template cache
			self._template_cache = {}
			self._template_cache_expiry = None
			
			return True
			
		except Exception as e:
			logger.error(f"Failed to delete DocuSign template: {e}")
			return False

	def _parse_docusign_date(self, date_str: Optional[str]) -> Optional[datetime]:
		"""Parse DocuSign date string to datetime object"""
		if not date_str:
			return None
		
		try:
			# DocuSign typically uses ISO format
			return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
		except:
			try:
				# Fallback to common formats
				return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
			except:
				logger.warning(f"Could not parse DocuSign date: {date_str}")
				return None

	def _verify_webhook_signature(self, payload: str, signature: str) -> bool:
		"""Verify DocuSign webhook signature for security"""
		if not self.webhook_secret:
			logger.warning("Webhook secret not configured, skipping signature verification")
			return True
		
		try:
			expected_signature = hmac.new(
				self.webhook_secret.encode('utf-8'),
				payload.encode('utf-8'),
				hashlib.sha256
			).hexdigest()
			
			# DocuSign uses base64 encoded signature
			import base64
			signature_bytes = base64.b64decode(signature)
			expected_signature_bytes = bytes.fromhex(expected_signature)
			
			return hmac.compare_digest(signature_bytes, expected_signature_bytes)
		except Exception as e:
			logger.error(f"Webhook signature verification failed: {e}")
			return False

	async def handle_webhook(self, payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, Any]:
		"""Handle incoming webhook notifications from DocuSign with enhanced processing"""
		webhook_result = {
			"processed": False,
			"envelope_id": None,
			"event": None,
			"error": None
		}
		
		try:
			# Verify webhook signature if provided
			if signature:
				payload_str = json.dumps(payload, sort_keys=True)
				if not self._verify_webhook_signature(payload_str, signature):
					error_msg = "Invalid webhook signature"
					self._log_audit_event(f"Webhook signature verification failed")
					logger.error(error_msg)
					webhook_result["error"] = error_msg
					return webhook_result
			
			# Parse webhook event
			event = payload.get("event", "unknown")
			envelope_id = payload.get("envelopeId")
			status = payload.get("status")
			
			webhook_result["event"] = event
			webhook_result["envelope_id"] = envelope_id
			
			self._log_audit_event(
				f"Webhook received: {event}",
				envelope_id=envelope_id,
				additional_data={"status": status, "event": event}
			)
			
			logger.info(f"Processing DocuSign webhook: event={event}, envelope={envelope_id}, status={status}")
			
			# Process different webhook events
			if event in ["envelope-sent", "envelope-delivered", "envelope-completed", 
						"envelope-declined", "envelope-voided", "recipient-completed"]:
				
				if envelope_id and status:
					# Update envelope status in database
					async with get_db_session() as db_session:
						envelope_repo = DocuSignEnvelopeRepository(db_session)
						updated_envelope = await envelope_repo.update_envelope_status(
							envelope_id=envelope_id, 
							status=status
						)
						
						if updated_envelope:
							self._log_audit_event(
								f"Envelope status updated to {status}",
								envelope_id=envelope_id
							)
						else:
							logger.warning(f"Envelope {envelope_id} not found in database")
				
				# Handle specific events
				if event == "envelope-completed":
					await self._handle_envelope_completed(envelope_id, payload)
				elif event == "envelope-declined":
					await self._handle_envelope_declined(envelope_id, payload)
				elif event == "envelope-voided":
					await self._handle_envelope_voided(envelope_id, payload)
				elif event == "recipient-completed":
					await self._handle_recipient_completed(envelope_id, payload)
			
			webhook_result["processed"] = True
			logger.info(f"DocuSign webhook processed successfully: {event}")
			
		except Exception as e:
			error_msg = f"Error handling DocuSign webhook: {str(e)}"
			self._log_audit_event(error_msg, envelope_id=webhook_result.get("envelope_id"))
			logger.error(error_msg)
			webhook_result["error"] = error_msg
		
		return webhook_result

	async def _handle_envelope_completed(self, envelope_id: str, payload: Dict[str, Any]) -> None:
		"""Handle envelope completion event"""
		try:
			# Download completed documents for archival
			documents = await self.get_envelope_documents(envelope_id)
			if documents:
				for doc in documents:
					doc_id = doc.get("documentId")
					if doc_id and doc_id != "certificate":  # Skip certificate document
						document_content = await self.download_completed_document(envelope_id, doc_id)
						if document_content:
							# Store completed document (implement storage logic as needed)
							self._log_audit_event(
								f"Completed document downloaded",
								envelope_id=envelope_id,
								additional_data={"document_id": doc_id}
							)
			
			# Get audit trail
			audit_events = await self.get_envelope_audit_events(envelope_id)
			if audit_events:
				self._log_audit_event(
					"Audit trail retrieved for completed envelope",
					envelope_id=envelope_id,
					additional_data={"audit_event_count": len(audit_events)}
				)
			
		except Exception as e:
			logger.error(f"Error handling envelope completion: {e}")

	async def _handle_envelope_declined(self, envelope_id: str, payload: Dict[str, Any]) -> None:
		"""Handle envelope decline event"""
		try:
			decline_reason = payload.get("declineReason", "No reason provided")
			recipient_email = payload.get("recipientEmail", "Unknown")
			
			self._log_audit_event(
				f"Envelope declined by {recipient_email}",
				envelope_id=envelope_id,
				additional_data={"decline_reason": decline_reason}
			)
			
			# Implement notification logic as needed
			logger.info(f"Envelope {envelope_id} declined by {recipient_email}: {decline_reason}")
			
		except Exception as e:
			logger.error(f"Error handling envelope decline: {e}")

	async def _handle_envelope_voided(self, envelope_id: str, payload: Dict[str, Any]) -> None:
		"""Handle envelope void event"""
		try:
			void_reason = payload.get("voidedReason", "No reason provided")
			
			self._log_audit_event(
				f"Envelope voided",
				envelope_id=envelope_id,
				additional_data={"void_reason": void_reason}
			)
			
			logger.info(f"Envelope {envelope_id} voided: {void_reason}")
			
		except Exception as e:
			logger.error(f"Error handling envelope void: {e}")

	async def _handle_recipient_completed(self, envelope_id: str, payload: Dict[str, Any]) -> None:
		"""Handle recipient completion event"""
		try:
			recipient_email = payload.get("recipientEmail", "Unknown")
			recipient_status = payload.get("recipientStatus", "Unknown")
			
			self._log_audit_event(
				f"Recipient {recipient_email} completed signing",
				envelope_id=envelope_id,
				additional_data={"recipient_status": recipient_status}
			)
			
			logger.info(f"Recipient {recipient_email} completed signing envelope {envelope_id}")
			
		except Exception as e:
			logger.error(f"Error handling recipient completion: {e}")

	async def get_envelope_recipients(self, envelope_id: str) -> Optional[List[Dict[str, Any]]]:
		"""Get envelope recipients and their status"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/recipients",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.json()
		except Exception as e:
			logger.error(f"Failed to get envelope recipients: {e}")
			return None

	async def get_envelope_documents(self, envelope_id: str) -> Optional[List[Dict[str, Any]]]:
		"""Get list of documents in an envelope"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/documents",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.json().get("envelopeDocuments", [])
		except Exception as e:
			logger.error(f"Failed to get envelope documents: {e}")
			return None

	async def download_completed_document(self, envelope_id: str, document_id: str = "combined") -> Optional[bytes]:
		"""Download completed document with signatures"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				response = await client.get(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/documents/{document_id}",
					headers={"Authorization": f"Bearer {self.access_token}"},
				)
				response.raise_for_status()
				return response.content
		except Exception as e:
			logger.error(f"Failed to download completed document: {e}")
			return None

	async def resend_envelope(self, envelope_id: str) -> bool:
		"""Resend envelope to recipients"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return False

		try:
			async with httpx.AsyncClient() as client:
				response = await client.put(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}",
					headers={
						"Authorization": f"Bearer {self.access_token}",
						"Content-Type": "application/json",
					},
					json={"resendEnvelope": "true"},
				)
				response.raise_for_status()
				logger.info(f"DocuSign: Resent envelope {envelope_id}")
				return True
		except Exception as e:
			logger.error(f"Failed to resend DocuSign envelope: {e}")
			return False

	async def get_envelope_audit_events(self, envelope_id: str) -> Optional[List[DocuSignAuditEvent]]:
		"""Get audit events for an envelope with enhanced processing"""
		try:
			response = await self._make_api_request(
				"GET",
				f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/audit_events"
			)
			
			audit_data = response.json()
			raw_events = audit_data.get("auditEvents", [])
			
			# Convert to structured audit events
			audit_events = []
			for event_data in raw_events:
				try:
					audit_event = DocuSignAuditEvent(
						event_timestamp=self._parse_docusign_date(event_data.get("eventTimestamp")) or datetime.now(),
						event_description=event_data.get("eventDescription", "Unknown event"),
						user_name=event_data.get("userName"),
						user_id=event_data.get("userId"),
						client_ip=event_data.get("clientIPAddress"),
						geo_location=event_data.get("geoLocation")
					)
					audit_events.append(audit_event)
				except Exception as e:
					logger.warning(f"Failed to parse audit event: {e}")
					continue
			
			self._log_audit_event(
				f"Retrieved {len(audit_events)} audit events",
				envelope_id=envelope_id
			)
			
			return audit_events
			
		except Exception as e:
			logger.error(f"Failed to get envelope audit events: {e}")
			return None

	async def store_audit_trail(self, envelope_id: str) -> Optional[Dict[str, Any]]:
		"""Store complete audit trail for an envelope including certificate of completion"""
		try:
			# Get audit events
			audit_events = await self.get_envelope_audit_events(envelope_id)
			
			# Get certificate of completion
			certificate = await self.get_certificate_of_completion(envelope_id)
			
			# Get envelope details
			envelope_status = await self.get_envelope_status(envelope_id)
			
			# Compile complete audit trail
			audit_trail = {
				"envelope_id": envelope_id,
				"generated_at": datetime.now().isoformat(),
				"envelope_status": envelope_status,
				"audit_events": [
					{
						"timestamp": event.event_timestamp.isoformat(),
						"description": event.event_description,
						"user_name": event.user_name,
						"user_id": event.user_id,
						"client_ip": event.client_ip,
						"geo_location": event.geo_location
					}
					for event in (audit_events or [])
				],
				"certificate_of_completion": certificate
			}
			
			# Store audit trail (implement storage logic as needed)
			# This could be stored in database, file system, or cloud storage
			await self._store_audit_trail_data(envelope_id, audit_trail)
			
			self._log_audit_event(
				"Complete audit trail stored",
				envelope_id=envelope_id,
				additional_data={
					"audit_event_count": len(audit_events or []),
					"has_certificate": certificate is not None
				}
			)
			
			return audit_trail
			
		except Exception as e:
			logger.error(f"Failed to store audit trail: {e}")
			return None

	async def get_certificate_of_completion(self, envelope_id: str) -> Optional[bytes]:
		"""Get certificate of completion for an envelope"""
		try:
			response = await self._make_api_request(
				"GET",
				f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/documents/certificate"
			)
			
			return response.content
			
		except Exception as e:
			logger.error(f"Failed to get certificate of completion: {e}")
			return None

	async def _store_audit_trail_data(self, envelope_id: str, audit_trail: Dict[str, Any]) -> None:
		"""Store audit trail data (implement based on storage requirements)"""
		try:
			# This is a placeholder - implement actual storage logic
			# Options: Database, file system, cloud storage (S3, Azure Blob, etc.)
			
			# Example: Store in database
			async with get_db_session() as db_session:
				# Create audit trail record in database
				# This would require a new table/model for audit trails
				pass
			
			# Example: Store as JSON file
			# import json
			# audit_file_path = f"audit_trails/{envelope_id}_audit.json"
			# with open(audit_file_path, 'w') as f:
			#     json.dump(audit_trail, f, indent=2)
			
			logger.info(f"Audit trail stored for envelope {envelope_id}")
			
		except Exception as e:
			logger.error(f"Failed to store audit trail data: {e}")

	async def get_compliance_report(
		self,
		envelope_ids: List[str],
		include_documents: bool = False
	) -> Dict[str, Any]:
		"""Generate compliance report for multiple envelopes"""
		try:
			compliance_report = {
				"generated_at": datetime.now().isoformat(),
				"envelope_count": len(envelope_ids),
				"envelopes": [],
				"summary": {
					"completed": 0,
					"pending": 0,
					"declined": 0,
					"voided": 0
				}
			}
			
			for envelope_id in envelope_ids:
				try:
					# Get envelope status
					status_data = await self.get_envelope_status(envelope_id)
					status = status_data.get("status", "unknown") if status_data else "unknown"
					
					envelope_report = {
						"envelope_id": envelope_id,
						"status": status,
						"created_date": status_data.get("createdDateTime") if status_data else None,
						"completed_date": status_data.get("completedDateTime") if status_data else None
					}
					
					# Get audit events
					audit_events = await self.get_envelope_audit_events(envelope_id)
					envelope_report["audit_event_count"] = len(audit_events or [])
					
					# Include documents if requested
					if include_documents and status == "completed":
						documents = await self.get_envelope_documents(envelope_id)
						envelope_report["document_count"] = len(documents or [])
					
					compliance_report["envelopes"].append(envelope_report)
					
					# Update summary
					if status == "completed":
						compliance_report["summary"]["completed"] += 1
					elif status in ["sent", "delivered"]:
						compliance_report["summary"]["pending"] += 1
					elif status == "declined":
						compliance_report["summary"]["declined"] += 1
					elif status == "voided":
						compliance_report["summary"]["voided"] += 1
					
				except Exception as e:
					logger.error(f"Failed to process envelope {envelope_id} for compliance report: {e}")
					continue
			
			self._log_audit_event(
				f"Compliance report generated for {len(envelope_ids)} envelopes",
				additional_data=compliance_report["summary"]
			)
			
			return compliance_report
			
		except Exception as e:
			logger.error(f"Failed to generate compliance report: {e}")
			return {
				"error": str(e),
				"generated_at": datetime.now().isoformat(),
				"envelope_count": 0,
				"envelopes": [],
				"summary": {}
			}

	async def export_audit_logs(
		self,
		start_date: datetime,
		end_date: datetime,
		format_type: str = "json"
	) -> Optional[Union[str, bytes]]:
		"""Export audit logs for a date range"""
		try:
			# Filter audit events by date range
			filtered_events = [
				event for event in self._audit_events
				if start_date <= datetime.fromisoformat(event["timestamp"]) <= end_date
			]
			
			if format_type.lower() == "json":
				import json
				return json.dumps(filtered_events, indent=2)
			elif format_type.lower() == "csv":
				import csv
				import io
				
				output = io.StringIO()
				if filtered_events:
					fieldnames = filtered_events[0].keys()
					writer = csv.DictWriter(output, fieldnames=fieldnames)
					writer.writeheader()
					writer.writerows(filtered_events)
				
				return output.getvalue()
			else:
				raise DocuSignError(f"Unsupported export format: {format_type}", "INVALID_FORMAT")
			
		except Exception as e:
			logger.error(f"Failed to export audit logs: {e}")
			return None

	async def create_embedded_signing_view(
		self, 
		envelope_id: str, 
		recipient_email: str, 
		recipient_name: str, 
		return_url: str,
		client_user_id: Optional[str] = None
	) -> Optional[str]:
		"""Create embedded signing view for recipient"""
		if not await self._ensure_authenticated():
			logger.error("DocuSign authentication failed")
			return None

		try:
			async with httpx.AsyncClient() as client:
				payload = {
					"returnUrl": return_url,
					"authenticationMethod": "none",
					"email": recipient_email,
					"userName": recipient_name,
				}
				
				if client_user_id:
					payload["clientUserId"] = client_user_id

				response = await client.post(
					f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/views/recipient",
					headers={
						"Authorization": f"Bearer {self.access_token}",
						"Content-Type": "application/json",
					},
					json=payload,
				)
				response.raise_for_status()
				view_data = response.json()
				return view_data["url"]
		except Exception as e:
			logger.error(f"Failed to create embedded signing view: {e}")
			return None

	async def create_envelope_from_template(
		self,
		template_id: str,
		recipients: List[DocuSignRecipient],
		email_subject: str,
		email_blurb: str,
		custom_fields: Optional[Dict[str, Any]] = None,
		auto_send: bool = False
	) -> Optional[str]:
		"""Create envelope from template with enhanced workflow automation"""
		try:
			# Validate template exists
			templates = await self.get_templates()
			template_exists = any(t.template_id == template_id for t in templates)
			
			if not template_exists:
				raise DocuSignError(f"Template {template_id} not found", "TEMPLATE_NOT_FOUND")
			
			envelope_data = {
				"templateId": template_id,
				"emailSubject": email_subject,
				"emailBlurb": email_blurb,
				"status": "sent" if auto_send else "created",
				"templateRoles": []
			}
			
			# Process recipients with enhanced validation
			for i, recipient in enumerate(recipients):
				role_data = {
					"email": recipient.email,
					"name": recipient.name,
					"roleName": recipient.role,
					"routingOrder": str(recipient.routing_order),
				}
				
				if recipient.client_user_id:
					role_data["clientUserId"] = recipient.client_user_id
				
				if recipient.access_code:
					role_data["accessCode"] = recipient.access_code
				
				if recipient.id_check_required:
					role_data["requireIdLookup"] = True
				
				if recipient.phone_authentication:
					role_data["phoneAuthentication"] = recipient.phone_authentication
				
				if recipient.sms_authentication:
					role_data["smsAuthentication"] = recipient.sms_authentication
				
				envelope_data["templateRoles"].append(role_data)

			# Add custom fields
			if custom_fields:
				envelope_data["customFields"] = {
					"textCustomFields": [
						{"name": key, "value": str(value)} 
						for key, value in custom_fields.items()
					]
				}
			
			# Add workflow settings
			envelope_data["notification"] = {
				"useAccountDefaults": True,
				"reminders": {
					"reminderEnabled": True,
					"reminderDelay": 2,
					"reminderFrequency": 2
				},
				"expirations": {
					"expireEnabled": True,
					"expireAfter": 30,
					"expireWarn": 5
				}
			}

			response = await self._make_api_request(
				"POST",
				f"{self.base_url}/accounts/{self.account_id}/envelopes",
				json_data=envelope_data
			)
			
			envelope_response = response.json()
			envelope_id = envelope_response["envelopeId"]
			
			self._log_audit_event(
				f"Envelope created from template {template_id}",
				envelope_id=envelope_id,
				additional_data={
					"template_id": template_id,
					"auto_send": auto_send,
					"recipient_count": len(recipients)
				}
			)
			
			logger.info(f"DocuSign: Created envelope from template {envelope_id}")
			return envelope_id
			
		except DocuSignError:
			raise
		except Exception as e:
			logger.error(f"Failed to create envelope from template: {e}")
			raise DocuSignError(f"Template envelope creation failed: {str(e)}", "TEMPLATE_CREATION_FAILED")

	async def create_signing_workflow(
		self,
		workflow_name: str,
		documents: List[DocuSignDocument],
		workflow_steps: List[Dict[str, Any]],
		email_subject: str,
		email_blurb: str,
		custom_fields: Optional[Dict[str, Any]] = None
	) -> Optional[str]:
		"""Create a multi-step signing workflow with sequential or parallel processing"""
		try:
			# Validate workflow steps
			if not workflow_steps:
				raise DocuSignError("Workflow must contain at least one step", "INVALID_WORKFLOW")
			
			# Build recipients from workflow steps
			recipients = []
			for step in workflow_steps:
				step_recipients = step.get("recipients", [])
				for recipient_data in step_recipients:
					recipient = DocuSignRecipient(
						email=recipient_data["email"],
						name=recipient_data["name"],
						role=recipient_data.get("role", "signer"),
						routing_order=step.get("order", 1),
						client_user_id=recipient_data.get("client_user_id"),
						access_code=recipient_data.get("access_code"),
						id_check_required=recipient_data.get("id_check_required", False)
					)
					recipients.append(recipient)
			
			# Create envelope
			envelope = DocuSignEnvelope(
				email_subject=email_subject,
				email_blurb=email_blurb,
				documents=documents,
				recipients=recipients,
				custom_fields=custom_fields or {},
				enforce_signer_visibility=True,
				allow_reassign=True
			)
			
			envelope_id = await self.create_envelope(envelope)
			
			if envelope_id:
				# Send envelope to start workflow
				await self.send_envelope(envelope_id)
				
				self._log_audit_event(
					f"Signing workflow created: {workflow_name}",
					envelope_id=envelope_id,
					additional_data={
						"workflow_steps": len(workflow_steps),
						"total_recipients": len(recipients)
					}
				)
			
			return envelope_id
			
		except Exception as e:
			logger.error(f"Failed to create signing workflow: {e}")
			return None

	async def bulk_send_envelopes(
		self,
		template_id: str,
		bulk_recipients: List[List[DocuSignRecipient]],
		email_subject: str,
		email_blurb: str,
		custom_fields_list: Optional[List[Dict[str, Any]]] = None
	) -> List[Optional[str]]:
		"""Send multiple envelopes in bulk for mass signing campaigns"""
		envelope_ids = []
		
		try:
			for i, recipients in enumerate(bulk_recipients):
				custom_fields = None
				if custom_fields_list and i < len(custom_fields_list):
					custom_fields = custom_fields_list[i]
				
				try:
					envelope_id = await self.create_envelope_from_template(
						template_id=template_id,
						recipients=recipients,
						email_subject=email_subject,
						email_blurb=email_blurb,
						custom_fields=custom_fields,
						auto_send=True
					)
					envelope_ids.append(envelope_id)
					
					# Add delay to respect rate limits
					await asyncio.sleep(0.1)
					
				except Exception as e:
					logger.error(f"Failed to create bulk envelope {i}: {e}")
					envelope_ids.append(None)
			
			successful_sends = sum(1 for eid in envelope_ids if eid is not None)
			self._log_audit_event(
				f"Bulk send completed: {successful_sends}/{len(bulk_recipients)} successful",
				additional_data={
					"template_id": template_id,
					"total_envelopes": len(bulk_recipients),
					"successful": successful_sends
				}
			)
			
			return envelope_ids
			
		except Exception as e:
			logger.error(f"Bulk send operation failed: {e}")
			return envelope_ids

	async def schedule_envelope_reminder(
		self,
		envelope_id: str,
		reminder_delay_days: int = 2,
		reminder_frequency_days: int = 2
	) -> bool:
		"""Schedule automatic reminders for an envelope"""
		try:
			reminder_data = {
				"reminders": {
					"reminderEnabled": True,
					"reminderDelay": reminder_delay_days,
					"reminderFrequency": reminder_frequency_days
				}
			}
			
			response = await self._make_api_request(
				"PUT",
				f"{self.base_url}/accounts/{self.account_id}/envelopes/{envelope_id}/notification",
				json_data=reminder_data
			)
			
			self._log_audit_event(
				f"Reminder scheduled for envelope",
				envelope_id=envelope_id,
				additional_data={
					"reminder_delay": reminder_delay_days,
					"reminder_frequency": reminder_frequency_days
				}
			)
			
			return True
			
		except Exception as e:
			logger.error(f"Failed to schedule envelope reminder: {e}")
			return False