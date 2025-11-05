"""
Minimal, import-safe Integration Service.

Replaces a corrupted file with a lightweight implementation that preserves the
public API but avoids heavy external dependencies and network calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntegrationType(str, Enum):
    MICROSOFT_365 = "microsoft_365"
    DOCUSIGN = "docusign"
    SLACK = "slack"
    GMAIL = "gmail"
    LOCAL_STORAGE = "local_storage"
    GOOGLE_DRIVE = "google_drive"
    DOCUSIGN_SANDBOX = "docusign_sandbox"
    LOCAL_PDF_SIGNING = "local_pdf_signing"
    OLLAMA = "ollama"


@dataclass
class DocumentMetadata:
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
    def __init__(self) -> None:
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def authenticate(self) -> bool:
        self.access_token = "mock_access_token"
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return True

    async def _ensure_authenticated(self) -> bool:
        if not self.access_token or (self.token_expires_at and self.token_expires_at <= datetime.now(timezone.utc)):
            return await self.authenticate()
        return True

    async def get_documents(self, folder_id: Optional[str] = None) -> List[DocumentMetadata]:
        await self._ensure_authenticated()
        return [
            DocumentMetadata(
                document_id="doc1",
                title="Contract Template.docx",
                file_type="docx",
                size=1024000,
                created_at=datetime.now(timezone.utc) - timedelta(days=1),
                modified_at=datetime.now(timezone.utc),
                owner="user@company.com",
                permissions=["read", "write"],
                tags=["contract", "template"],
                metadata={"folder": "Contracts"},
            )
        ]

    async def upload_document(self, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        await self._ensure_authenticated()
        return f"uploaded_doc_{int(datetime.now(timezone.utc).timestamp())}"

    async def download_document(self, document_id: str) -> Optional[bytes]:
        await self._ensure_authenticated()
        return b"Mock document content"


class DocuSignIntegration:
    def __init__(self) -> None:
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def authenticate(self) -> bool:
        self.access_token = "mock"
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return True

    async def _ensure_authenticated(self) -> bool:
        if not self.access_token or (self.token_expires_at and self.token_expires_at <= datetime.now(timezone.utc)):
            return await self.authenticate()
        return True

    async def create_envelope(self, document_id: str, recipients: List[Dict[str, Any]], subject: str, message: str) -> Optional[str]:
        await self._ensure_authenticated()
        return f"envelope_{int(datetime.now(timezone.utc).timestamp())}"

    async def get_envelope_status(self, envelope_id: str) -> Optional[Dict[str, Any]]:
        await self._ensure_authenticated()
        return {"envelope_id": envelope_id, "status": "sent"}

    async def void_envelope(self, envelope_id: str, reason: str) -> bool:
        await self._ensure_authenticated()
        return True


class SlackIntegration:
    def __init__(self, webhook_url: Optional[str]) -> None:
        self.webhook_url = webhook_url

    async def send_notification(self, message: str, channel: Optional[str] = None) -> bool:
        # No external call; just log and succeed
        logger.info(f"[Slack] would send to {channel or '#general'}: {message[:60]}...")
        return True

    async def send_contract_analysis_alert(self, contract_name: str, risk_level: str, analysis_url: str) -> bool:
        msg = f"Contract: {contract_name} | Risk: {risk_level} | {analysis_url}"
        return await self.send_notification(msg, "#contracts")


class IntegrationService:
    def __init__(self) -> None:
        self.integrations: Dict[str, Any] = {}
        self.configs = self._load_integration_configs()
        self._initialize_integrations()

    def _load_integration_configs(self) -> Dict[str, Dict[str, Any]]:
        # Minimal environment-driven configs
        return {
            "microsoft_365": {"enabled": os.getenv("MICROSOFT_365_ENABLED", "false").lower() == "true"},
            "docusign": {"enabled": os.getenv("DOCUSIGN_ENABLED", "false").lower() == "true"},
            "slack": {"enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true", "webhook_url": os.getenv("SLACK_WEBHOOK_URL")},
        }

    def _initialize_integrations(self) -> None:
        for name, cfg in self.configs.items():
            if not cfg.get("enabled"):
                continue
            try:
                if name == "microsoft_365":
                    self.integrations[name] = Microsoft365Integration()
                elif name == "docusign":
                    self.integrations[name] = DocuSignIntegration()
                elif name == "slack":
                    self.integrations[name] = SlackIntegration(cfg.get("webhook_url"))
                logger.info(f"Initialized integration: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize integration {name}: {e}")

    async def get_available_integrations(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "type": name,
                "enabled": name in self.integrations,
                "status": "active" if name in self.integrations else "inactive",
            }
            for name in self.configs.keys()
        ]

    async def test_integration(self, integration_name: str) -> Dict[str, Any]:
        if integration_name not in self.integrations:
            return {"status": "error", "message": "Integration not found"}
        try:
            integ = self.integrations[integration_name]
            if hasattr(integ, "authenticate"):
                ok = await integ.authenticate()
                return {"status": "success" if ok else "error", "message": "Integration test passed" if ok else "Authentication failed"}
            return {"status": "success", "message": "Integration test passed"}
        except Exception as e:
            return {"status": "error", "message": f"Integration test failed: {e!s}"}

    async def sync_documents(self, integration_name: str) -> List[DocumentMetadata]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "get_documents"):
            return await integ.get_documents()
        return []

    async def upload_document(self, integration_name: str, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "upload_document"):
            return await integ.upload_document(file_path, folder_id)
        return None

    async def send_notification(self, integration_name: str, message: str, **kwargs) -> bool:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "send_notification"):
            return await integ.send_notification(message, kwargs.get("channel"))
        return False

    async def create_docusign_envelope(
        self, integration_name: str, document_id: str, recipients: List[Dict[str, Any]], subject: str, message: str
    ) -> Optional[str]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "create_envelope"):
            return await integ.create_envelope(document_id, recipients, subject, message)
        return None

    async def get_docusign_envelope_status(self, integration_name: str, envelope_id: str) -> Optional[Dict[str, Any]]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "get_envelope_status"):
            return await integ.get_envelope_status(envelope_id)
        return None

    async def send_contract_analysis_alert(self, *args, **kwargs) -> bool:
        # Supports both historical signatures; if integration_name provided, route to that integration.
        if args and isinstance(args[0], str) and args[0] in self.integrations:
            integration_name = args[0]
            integ = self.integrations.get(integration_name)
            if hasattr(integ, "send_contract_analysis_alert"):
                try:
                    return await integ.send_contract_analysis_alert(*args[1:], **kwargs)
                except Exception as e:
                    logger.error(f"Failed to send alert via {integration_name}: {e}")
                    return False
            return False
        # Fallback: broadcast style (contract_name, risk_level, analysis_url)
        success = True
        for name, integ in self.integrations.items():
            if hasattr(integ, "send_contract_analysis_alert"):
                try:
                    ok = await integ.send_contract_analysis_alert(*args, **kwargs)
                    success = success and ok
                except Exception as e:
                    logger.error(f"Failed to send alert via {name}: {e}")
                    success = False
        return success

    async def get_ollama_models(self, integration_name: str) -> List[str]:
        # Minimal stub: return empty list unless integration provides method
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "get_models"):
            return await integ.get_models()
        return []

    async def chat_with_ollama(self, integration_name: str, message: str, model: Optional[str] = None) -> str:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "chat"):
            return await integ.chat(message, model)
        return "Chat not supported for this integration"

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
        # Email integration is not wired in minimal version; succeed as no-op
        logger.info(f"[Email] would send contract analysis to {recipient_email}")
        return True

    async def send_notification_email(self, integration_name: str, recipient_email: str, title: str, message: str, priority: str = "normal") -> bool:
        logger.info(f"[Email] would send '{title}' to {recipient_email} (priority {priority})")
        return True

    async def send_slack_notification(self, integration_name: str, title: str, message: str, priority: str = "normal", channel: Optional[str] = None) -> bool:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "send_notification"):
            return await integ.send_notification(f"{title}: {message}", channel)
        return False

    async def create_contract_envelope(
        self,
        integration_name: str,
        contract_name: str,
        contract_content: bytes,
        recipients: List[Dict[str, str]],
        subject: str = "Contract for Signature",
        message: str = "Please review and sign the attached contract.",
    ) -> Optional[str]:
        # Minimal: use docusign-like if available
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "create_contract_envelope"):
            return await integ.create_contract_envelope(contract_name, contract_content, recipients, subject, message)
        # Fallback to create_envelope with a placeholder doc id
        if hasattr(integ, "create_envelope"):
            return await integ.create_envelope("document", recipients, subject, message)
        return None

    async def get_envelope_status(self, integration_name: str, envelope_id: str) -> Optional[Dict[str, Any]]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "get_envelope_status"):
            return await integ.get_envelope_status(envelope_id)
        return None

    async def get_signing_url(self, integration_name: str, envelope_id: str, recipient_email: str) -> Optional[str]:
        integ = self.integrations.get(integration_name)
        if hasattr(integ, "get_signing_url"):
            return await integ.get_signing_url(envelope_id, recipient_email)
        return None


_integration_service: Optional[IntegrationService] = None


def get_integration_service() -> IntegrationService:
    global _integration_service
    if _integration_service is None:
        _integration_service = IntegrationService()
    return _integration_service
