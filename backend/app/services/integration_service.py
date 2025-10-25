"""
Integration Service
Handles integrations with external services like Microsoft 365, DocuSign, and other platforms
"""

import asyncio
import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger
from .docusign_sandbox_service import DocuSignSandboxService
from .docusign_service import DocuSignService
from .email_service import EmailService
from .google_drive_service import GoogleDriveService
from .local_pdf_signing_service import LocalPDFSigningService
from .local_storage_service import LocalStorageService
from .ollama_service import OllamaService
from .slack_service import SlackService

logger = get_logger(__name__)
settings = get_settings()


class IntegrationType(str, Enum):
	"""Types of integrations supported"""

	MICROSOFT_365 = "microsoft_365"
	DOCUSIGN = "docusign"
	SALESFORCE = "salesforce"
	HUBSPOT = "hubspot"
	SLACK = "slack"
	TEAMS = "teams"
	GMAIL = "gmail"
	# Free alternatives
	LOCAL_STORAGE = "local_storage"
	GOOGLE_DRIVE = "google_drive"
	DOCUSIGN_SANDBOX = "docusign_sandbox"
	LOCAL_PDF_SIGNING = "local_pdf_signing"
	OLLAMA = "ollama"


class IntegrationStatus(str, Enum):
	"""Integration status"""

	ACTIVE = "active"
	INACTIVE = "inactive"
	ERROR = "error"
	PENDING = "pending"


@dataclass
class IntegrationConfig:
	"""Integration configuration"""

	integration_type: IntegrationType
	name: str
	client_id: str
	client_secret: str
	tenant_id: Optional[str] = None
	redirect_uri: Optional[str] = None
	scopes: List[str] = None
	webhook_url: Optional[str] = None
	enabled: bool = True


@dataclass
class DocumentMetadata:
	"""Document metadata for integrations"""

	document_id: str
	title: str
	file_type: str
	size: int
	created_at: datetime
	modified_at: datetime
	owner: str
	permissions: List[str]
	tags: List[str]
	metadata: Dict[str, Any]


class Microsoft365Integration:
	"""Microsoft 365 integration handler"""

	def __init__(self, config: IntegrationConfig):
		self.config = config
		self.base_url = "https://graph.microsoft.com/v1.0"
		self.access_token = None
		self.token_expires_at = None

	async def authenticate(self) -> bool:
		"""Authenticate with Microsoft Graph API"""
		try:
			# In production, you would implement OAuth2 flow
			# For now, we'll use a placeholder
			self.access_token = "placeholder_token"
			self.token_expires_at = datetime.utcnow() + timedelta(hours=1)
			return True
		except Exception as e:
			logger.error(f"Microsoft 365 authentication failed: {e}")
			return False

	async def get_documents(self, folder_id: Optional[str] = None) -> List[DocumentMetadata]:
		"""Get documents from Microsoft 365"""
		try:
			if not await self._ensure_authenticated():
				return []

			# In production, you would make actual API calls
			# For now, return mock data
			return [
				DocumentMetadata(
					document_id="doc1",
					title="Contract Template.docx",
					file_type="docx",
					size=1024000,
					created_at=datetime.utcnow() - timedelta(days=1),
					modified_at=datetime.utcnow(),
					owner="user@company.com",
					permissions=["read", "write"],
					tags=["contract", "template"],
					metadata={"folder": "Contracts"},
				)
			]
		except Exception as e:
			logger.error(f"Failed to get Microsoft 365 documents: {e}")
			return []

	async def upload_document(self, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
		"""Upload document to Microsoft 365"""
		try:
			if not await self._ensure_authenticated():
				return None

			# In production, you would upload the file
			# For now, return a mock document ID
			return f"uploaded_doc_{datetime.utcnow().timestamp()}"
		except Exception as e:
			logger.error(f"Failed to upload document to Microsoft 365: {e}")
			return None

	async def download_document(self, document_id: str) -> Optional[bytes]:
		"""Download document from Microsoft 365"""
		try:
			if not await self._ensure_authenticated():
				return None

			# In production, you would download the file
			# For now, return mock data
			return b"Mock document content"
		except Exception as e:
			logger.error(f"Failed to download document from Microsoft 365: {e}")
			return None

	async def _ensure_authenticated(self) -> bool:
		"""Ensure we have a valid access token"""
		if not self.access_token or (self.token_expires_at and self.token_expires_at <= datetime.utcnow()):
			return await self.authenticate()
		return True


class DocuSignIntegration:
	"""DocuSign integration handler"""

	def __init__(self, config: IntegrationConfig):
		self.config = config
		self.base_url = "https://demo.docusign.net/restapi/v2.1"
		self.access_token = None
		self.token_expires_at = None

	async def authenticate(self) -> bool:
		"""Authenticate with DocuSign API"""
		try:
			# In production, you would implement OAuth2 flow
			# For now, we'll use a placeholder
			self.access_token = "placeholder_token"
			self.token_expires_at = datetime.utcnow() + timedelta(hours=1)
			return True
		except Exception as e:
			logger.error(f"DocuSign authentication failed: {e}")
			return False

	async def create_envelope(self, document_id: str, recipients: List[Dict[str, Any]], subject: str, message: str) -> Optional[str]:
		"""Create a DocuSign envelope"""
		try:
			if not await self._ensure_authenticated():
				return None

			# In production, you would create the envelope
			# For now, return a mock envelope ID
			return f"envelope_{datetime.utcnow().timestamp()}"
		except Exception as e:
			logger.error(f"Failed to create DocuSign envelope: {e}")
			return None

	async def get_envelope_status(self, envelope_id: str) -> Optional[Dict[str, Any]]:
		"""Get envelope status"""
		try:
			if not await self._ensure_authenticated():
				return None

			# In production, you would get the actual status
			# For now, return mock data
			return {
				"envelope_id": envelope_id,
				"status": "sent",
				"created": datetime.utcnow().isoformat(),
				"sent": datetime.utcnow().isoformat(),
				"recipients": [],
			}
		except Exception as e:
			logger.error(f"Failed to get DocuSign envelope status: {e}")
			return None

	async def void_envelope(self, envelope_id: str, reason: str) -> bool:
		"""Void a DocuSign envelope"""
		try:
			if not await self._ensure_authenticated():
				return False

			# In production, you would void the envelope
			return True
		except Exception as e:
			logger.error(f"Failed to void DocuSign envelope: {e}")
			return False

	async def _ensure_authenticated(self) -> bool:
		"""Ensure we have a valid access token"""
		if not self.access_token or (self.token_expires_at and self.token_expires_at <= datetime.utcnow()):
			return await self.authenticate()
		return True


class SlackIntegration:
	"""Slack integration handler"""

	def __init__(self, config: IntegrationConfig):
		self.config = config
		self.webhook_url = config.webhook_url

	async def send_notification(self, message: str, channel: Optional[str] = None) -> bool:
		"""Send notification to Slack"""
		try:
			if not self.webhook_url:
				logger.warning("Slack webhook URL not configured")
				return False

			payload = {"text": message, "channel": channel or "#general"}

			async with httpx.AsyncClient() as client:
				response = await client.post(self.webhook_url, json=payload)
				return response.status_code == 200
		except Exception as e:
			logger.error(f"Failed to send Slack notification: {e}")
			return False

	async def send_contract_analysis_alert(self, contract_name: str, risk_level: str, analysis_url: str) -> bool:
		"""Send job application tracking alert to Slack"""
		message = f"🔍 Contract Analysis Complete\n"
		message += f"**Contract:** {contract_name}\n"
		message += f"**Risk Level:** {risk_level}\n"
		message += f"**Analysis:** {analysis_url}"

		return await self.send_notification(message, "#contracts")


class IntegrationService:
	"""Main integration service managing all external integrations"""

	def __init__(self):
		self.integrations = {}
		self.configs = self._load_integration_configs()
		self._initialize_integrations()

	def _load_integration_configs(self) -> Dict[str, IntegrationConfig]:
		"""Load integration configurations"""
		configs = {}

		# Microsoft 365 configuration
		if os.getenv("MICROSOFT_365_CLIENT_ID"):
			configs["microsoft_365"] = IntegrationConfig(
				integration_type=IntegrationType.MICROSOFT_365,
				name="Microsoft 365",
				client_id=os.getenv("MICROSOFT_365_CLIENT_ID"),
				client_secret=os.getenv("MICROSOFT_365_CLIENT_SECRET"),
				tenant_id=os.getenv("MICROSOFT_365_TENANT_ID"),
				redirect_uri=os.getenv("MICROSOFT_365_REDIRECT_URI"),
				scopes=["Files.ReadWrite", "Sites.ReadWrite.All"],
				enabled=os.getenv("MICROSOFT_365_ENABLED", "false").lower() == "true",
			)

		# DocuSign configuration
		if os.getenv("DOCUSIGN_CLIENT_ID"):
			configs["docusign"] = IntegrationConfig(
				integration_type=IntegrationType.DOCUSIGN,
				name="DocuSign",
				client_id=os.getenv("DOCUSIGN_CLIENT_ID"),
				client_secret=os.getenv("DOCUSIGN_CLIENT_SECRET"),
				redirect_uri=os.getenv("DOCUSIGN_REDIRECT_URI"),
				scopes=["signature", "impersonation"],
				enabled=os.getenv("DOCUSIGN_ENABLED", "false").lower() == "true",
			)

		# Slack configuration
		if os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_BOT_TOKEN"):
			configs["slack"] = IntegrationConfig(
				integration_type=IntegrationType.SLACK,
				name="Slack",
				client_id="",  # Not needed for webhook
				client_secret="",  # Not needed for webhook
				webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
				enabled=os.getenv("SLACK_ENABLED", "false").lower() == "true",
			)

		# Gmail configuration
		if os.getenv("GMAIL_CLIENT_ID"):
			configs["gmail"] = IntegrationConfig(
				integration_type=IntegrationType.GMAIL,
				name="Gmail",
				client_id=os.getenv("GMAIL_CLIENT_ID"),
				client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
				redirect_uri=os.getenv("GMAIL_REDIRECT_URI"),
				scopes=["https://www.googleapis.com/auth/gmail.send"],
				enabled=os.getenv("GMAIL_ENABLED", "false").lower() == "true",
			)

		# Free alternatives configuration

		# Local Storage (always available)
		configs["local_storage"] = IntegrationConfig(
			integration_type=IntegrationType.LOCAL_STORAGE,
			name="Local Storage",
			client_id="",
			client_secret="",
			enabled=os.getenv("LOCAL_STORAGE_ENABLED", "true").lower() == "true",
		)

		# Google Drive
		if os.getenv("GOOGLE_DRIVE_CLIENT_ID"):
			configs["google_drive"] = IntegrationConfig(
				integration_type=IntegrationType.GOOGLE_DRIVE,
				name="Google Drive",
				client_id=os.getenv("GOOGLE_DRIVE_CLIENT_ID"),
				client_secret=os.getenv("GOOGLE_DRIVE_CLIENT_SECRET"),
				redirect_uri=os.getenv("GOOGLE_DRIVE_REDIRECT_URI"),
				scopes=[os.getenv("GOOGLE_DRIVE_SCOPES", "https://www.googleapis.com/auth/drive.file")],
				enabled=os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true",
			)

		# DocuSign Sandbox
		if os.getenv("DOCUSIGN_SANDBOX_CLIENT_ID"):
			configs["docusign_sandbox"] = IntegrationConfig(
				integration_type=IntegrationType.DOCUSIGN_SANDBOX,
				name="DocuSign Sandbox",
				client_id=os.getenv("DOCUSIGN_SANDBOX_CLIENT_ID"),
				client_secret=os.getenv("DOCUSIGN_SANDBOX_CLIENT_SECRET"),
				redirect_uri=os.getenv("DOCUSIGN_SANDBOX_REDIRECT_URI"),
				scopes=[os.getenv("DOCUSIGN_SANDBOX_SCOPES", "signature,impersonation")],
				enabled=os.getenv("DOCUSIGN_SANDBOX_ENABLED", "false").lower() == "true",
			)

		# Local PDF Signing (always available)
		configs["local_pdf_signing"] = IntegrationConfig(
			integration_type=IntegrationType.LOCAL_PDF_SIGNING,
			name="Local PDF Signing",
			client_id="",
			client_secret="",
			enabled=os.getenv("LOCAL_PDF_SIGNING_ENABLED", "true").lower() == "true",
		)

		# Ollama
		configs["ollama"] = IntegrationConfig(
			integration_type=IntegrationType.OLLAMA,
			name="Ollama",
			client_id="",
			client_secret="",
			enabled=os.getenv("OLLAMA_ENABLED", "false").lower() == "true",
		)

		return configs

	def _initialize_integrations(self) -> None:
		"""Initialize integration handlers"""
		for name, config in self.configs.items():
			if not config.enabled:
				continue

			try:
				if config.integration_type == IntegrationType.MICROSOFT_365:
					self.integrations[name] = Microsoft365Integration(config)
				elif config.integration_type == IntegrationType.DOCUSIGN:
					self.integrations[name] = DocuSignService()
				elif config.integration_type == IntegrationType.SLACK:
					self.integrations[name] = SlackService()
				elif config.integration_type == IntegrationType.GMAIL:
					self.integrations[name] = EmailService()
				# Free alternatives
				elif config.integration_type == IntegrationType.LOCAL_STORAGE:
					self.integrations[name] = LocalStorageService()
				elif config.integration_type == IntegrationType.GOOGLE_DRIVE:
					self.integrations[name] = GoogleDriveService()
				elif config.integration_type == IntegrationType.DOCUSIGN_SANDBOX:
					self.integrations[name] = DocuSignSandboxService()
				elif config.integration_type == IntegrationType.LOCAL_PDF_SIGNING:
					self.integrations[name] = LocalPDFSigningService()
				elif config.integration_type == IntegrationType.OLLAMA:
					self.integrations[name] = OllamaService()
				else:
					logger.warning(f"Unknown integration type: {config.integration_type}")

				logger.info(f"Initialized {config.name} integration")
			except Exception as e:
				logger.error(f"Failed to initialize {config.name} integration: {e}")

	async def get_available_integrations(self) -> List[Dict[str, Any]]:
		"""Get list of available integrations"""
		return [
			{
				"name": config.name,
				"type": config.integration_type.value,
				"enabled": config.enabled,
				"status": "active" if name in self.integrations else "inactive",
			}
			for name, config in self.configs.items()
		]

	async def test_integration(self, integration_name: str) -> Dict[str, Any]:
		"""Test integration connectivity"""
		if integration_name not in self.integrations:
			return {"status": "error", "message": "Integration not found"}

		try:
			integration = self.integrations[integration_name]

			if hasattr(integration, "authenticate"):
				success = await integration.authenticate()
				if success:
					return {"status": "success", "message": "Integration test passed"}
				else:
					return {"status": "error", "message": "Authentication failed"}
			else:
				return {"status": "success", "message": "Integration test passed"}
		except Exception as e:
			return {"status": "error", "message": f"Integration test failed: {e!s}"}

	async def sync_documents(self, integration_name: str) -> List[DocumentMetadata]:
		"""Sync documents from integration"""
		if integration_name not in self.integrations:
			return []

		try:
			integration = self.integrations[integration_name]

			if hasattr(integration, "get_documents"):
				return await integration.get_documents()
			else:
				return []
		except Exception as e:
			logger.error(f"Failed to sync documents from {integration_name}: {e}")
			return []

	async def upload_document(self, integration_name: str, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
		"""Upload document to integration"""
		if integration_name not in self.integrations:
			return None

		try:
			integration = self.integrations[integration_name]

			if hasattr(integration, "upload_document"):
				return await integration.upload_document(file_path, folder_id)
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to upload document to {integration_name}: {e}")
			return None

	async def send_notification(self, integration_name: str, message: str, **kwargs) -> bool:
		"""Send notification through integration"""
		if integration_name not in self.integrations:
			return False

		try:
			integration = self.integrations[integration_name]

			if hasattr(integration, "send_notification"):
				return await integration.send_notification(message, **kwargs)
			else:
				return False
		except Exception as e:
			logger.error(f"Failed to send notification via {integration_name}: {e}")
			return False

	async def create_docusign_envelope(self, document_id: str, recipients: List[Dict[str, Any]], subject: str, message: str) -> Optional[str]:
		"""Create DocuSign envelope"""
		if "docusign" not in self.integrations:
			return None

		try:
			integration = self.integrations["docusign"]
			return await integration.create_envelope(document_id, recipients, subject, message)
		except Exception as e:
			logger.error(f"Failed to create DocuSign envelope: {e}")
			return None

	async def get_docusign_envelope_status(self, envelope_id: str) -> Optional[Dict[str, Any]]:
		"""Get DocuSign envelope status"""
		if "docusign" not in self.integrations:
			return None

		try:
			integration = self.integrations["docusign"]
			return await integration.get_envelope_status(envelope_id)
		except Exception as e:
			logger.error(f"Failed to get DocuSign envelope status: {e}")
			return None

	async def send_contract_analysis_alert(self, contract_name: str, risk_level: str, analysis_url: str) -> bool:
		"""Send job application tracking alert to all enabled notification integrations"""
		success = True

		for name, integration in self.integrations.items():
			if hasattr(integration, "send_contract_analysis_alert"):
				try:
					result = await integration.send_contract_analysis_alert(contract_name, risk_level, analysis_url)
					if not result:
						success = False
				except Exception as e:
					logger.error(f"Failed to send alert via {name}: {e}")
					success = False

		return success

	# Free alternatives specific methods
	async def get_storage_stats(self, integration_name: str) -> Dict[str, Any]:
		"""Get storage statistics for an integration"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "get_storage_stats"):
					return await integration.get_storage_stats()
				else:
					return {"error": "Storage stats not supported for this integration"}
			else:
				return {"error": "Integration not found"}
		except Exception as e:
			logger.error(f"Failed to get storage stats for {integration_name}: {e}")
			return {"error": str(e)}

	async def get_docusign_account_info(self, integration_name: str) -> Dict[str, Any]:
		"""Get DocuSign account information"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "get_account_info"):
					return await integration.get_account_info()
				else:
					return {"error": "Account info not supported for this integration"}
			else:
				return {"error": "Integration not found"}
		except Exception as e:
			logger.error(f"Failed to get account info for {integration_name}: {e}")
			return {"error": str(e)}

	async def create_docusign_envelope(
		self, integration_name: str, document_id: str, recipients: List[Dict[str, Any]], subject: str, message: str
	) -> Optional[str]:
		"""Create DocuSign envelope"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "create_envelope"):
					return await integration.create_envelope(document_id, recipients, subject, message)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to create envelope for {integration_name}: {e}")
			return None

	async def create_pdf_signing_template(self, integration_name: str, template_name: str, template_data: Dict[str, Any]) -> Optional[str]:
		"""Create PDF signing template"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "create_template"):
					return await integration.create_template(template_name, template_data)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to create PDF signing template for {integration_name}: {e}")
			return None

	async def sign_pdf_document(self, integration_name: str, document_path: str, signature_data: Dict[str, Any]) -> Optional[str]:
		"""Sign PDF document"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "sign_document"):
					return await integration.sign_document(document_path, signature_data)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to sign PDF document for {integration_name}: {e}")
			return None

	async def get_ollama_models(self, integration_name: str) -> List[str]:
		"""Get available Ollama models"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "get_models"):
					return await integration.get_models()
				else:
					return []
			else:
				return []
		except Exception as e:
			logger.error(f"Failed to get Ollama models for {integration_name}: {e}")
			return []

	async def chat_with_ollama(self, integration_name: str, message: str, model: Optional[str] = None) -> str:
		"""Chat with Ollama model"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "chat"):
					return await integration.chat(message, model)
				else:
					return "Chat not supported for this integration"
			else:
				return "Integration not found"
		except Exception as e:
			logger.error(f"Failed to chat with Ollama for {integration_name}: {e}")
			return f"Error: {e!s}"

	# Gmail integration methods
	async def send_contract_analysis_email(
		self,
		integration_name: str,
		recipient_email: str,
		contract_name: str,
		risk_score: float,
		risky_clauses: List[Dict[str, Any]],
		analysis_summary: str,
		recommendations: List[str],
	) -> bool:
		"""Send job application tracking results via email"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "send_contract_analysis_email"):
					return await integration.send_contract_analysis_email(
						recipient_email, contract_name, risk_score, risky_clauses, analysis_summary, recommendations
					)
				else:
					return False
			else:
				return False
		except Exception as e:
			logger.error(f"Failed to send job application tracking email for {integration_name}: {e}")
			return False

	async def send_notification_email(self, integration_name: str, recipient_email: str, title: str, message: str, priority: str = "normal") -> bool:
		"""Send a notification email"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "send_notification_email"):
					return await integration.send_notification_email(recipient_email, title, message, priority)
				else:
					return False
			else:
				return False
		except Exception as e:
			logger.error(f"Failed to send notification email for {integration_name}: {e}")
			return False

	# Slack integration methods
	async def send_contract_analysis_alert(
		self,
		integration_name: str,
		contract_name: str,
		risk_score: float,
		risky_clauses: List[Dict[str, Any]],
		analysis_summary: str,
		analysis_url: Optional[str] = None,
	) -> bool:
		"""Send job application tracking alert to Slack"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "send_contract_analysis_alert"):
					return await integration.send_contract_analysis_alert(contract_name, risk_score, risky_clauses, analysis_summary, analysis_url)
				else:
					return False
			else:
				return False
		except Exception as e:
			logger.error(f"Failed to send job application tracking alert for {integration_name}: {e}")
			return False

	async def send_slack_notification(
		self, integration_name: str, title: str, message: str, priority: str = "normal", channel: Optional[str] = None
	) -> bool:
		"""Send a notification to Slack"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "send_notification"):
					return await integration.send_notification(title, message, priority, channel)
				else:
					return False
			else:
				return False
		except Exception as e:
			logger.error(f"Failed to send Slack notification for {integration_name}: {e}")
			return False

	# DocuSign integration methods
	async def create_contract_envelope(
		self,
		integration_name: str,
		contract_name: str,
		contract_content: bytes,
		recipients: List[Dict[str, str]],
		subject: str = "Contract for Signature",
		message: str = "Please review and sign the attached contract.",
	) -> Optional[str]:
		"""Create a contract envelope for signing"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "create_contract_envelope"):
					return await integration.create_contract_envelope(contract_name, contract_content, recipients, subject, message)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to create contract envelope for {integration_name}: {e}")
			return None

	async def get_envelope_status(self, integration_name: str, envelope_id: str) -> Optional[Dict[str, Any]]:
		"""Get envelope status"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "get_envelope_status"):
					return await integration.get_envelope_status(envelope_id)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to get envelope status for {integration_name}: {e}")
			return None

	async def get_signing_url(self, integration_name: str, envelope_id: str, recipient_email: str) -> Optional[str]:
		"""Get signing URL for a recipient"""
		try:
			if integration_name in self.integrations:
				integration = self.integrations[integration_name]
				if hasattr(integration, "get_signing_url"):
					return await integration.get_signing_url(envelope_id, recipient_email)
				else:
					return None
			else:
				return None
		except Exception as e:
			logger.error(f"Failed to get signing URL for {integration_name}: {e}")
			return None


# Global integration service instance
_integration_service: Optional[IntegrationService] = None


def get_integration_service() -> IntegrationService:
	"""Get global integration service instance"""
	global _integration_service
	if _integration_service is None:
		_integration_service = IntegrationService()
	return _integration_service
